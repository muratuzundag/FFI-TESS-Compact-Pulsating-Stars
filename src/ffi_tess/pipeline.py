"""Coverage reporting, per-sector extraction and reproducible output."""
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path

import numpy as np

from .archive import discover, target_coordinates
from .core import cadence_seconds, clean_indices, normalize_flux
from .eleanor_adapter import extract
from .spectrum import calculate


def write_json(path,data):
    Path(path).write_text(json.dumps(data,indent=2,default=str,allow_nan=False))


def write_csv(path,rows,fields):
    with Path(path).open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


def plots(prefix,result,t,raw,selected,frequency,power,raw_power):
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(11,10))
    axes[0].imshow(result["median_image"],origin="lower",cmap="magma")
    if np.ptp(result["aperture"])>0:
        axes[0].contour(result["aperture"],levels=[.5],colors="cyan",linewidths=1)
    axes[0].set(xlabel="TPF column (pixel)",ylabel="TPF row (pixel)",title="Median image and aperture")
    axes[1].plot(t,raw,".",ms=1,color="0.65",label="Raw aperture")
    axes[1].plot(t,selected,".",ms=1,color="navy",label="Selected correction")
    axes[1].set(xlabel="eleanor time: BJD_TDB - 2457000 (d)",ylabel="Relative flux (ppt)")
    axes[1].legend(frameon=False)
    axes[2].plot(frequency,raw_power,color="0.7",lw=.7,label="Raw")
    axes[2].plot(frequency,power,color="navy",lw=.7,label="Selected")
    axes[2].set(xlabel=r"Frequency ($\mu$Hz)",ylabel="LS power (standard)")
    axes[2].legend(frameon=False)
    fig.tight_layout();fig.savefig(str(prefix)+"_diagnostics.png",dpi=200);plt.close(fig)


def process_sector(target,sector,expected,args,out):
    prefix=out/f"s{sector:04d}"
    result=extract(target,sector,args)
    if (result["camera"],result["ccd"])!=(expected["camera"],expected["ccd"]):
        raise ValueError("eleanor detector differs from coverage query; review source localization")
    time=result["time_btjd"]
    cadence=cadence_seconds(time)
    idx=clean_indices(time,result["raw_flux"],result["selected_flux"],result["quality"],
                       args.keep_flagged,args.sigma)
    used=np.zeros(len(time),dtype=bool);used[idx]=True
    np.savez_compressed(str(prefix)+"_extraction.npz",**{
        key:result[key] for key in ["time_btjd","raw_flux","standard_flux","pca_flux",
                                   "selected_flux","raw_flux_err","quality","median_image","aperture"]},
                        used_for_analysis=used)
    np.save(str(prefix)+"_aperture.npy",result["aperture"])
    raw,raw_median=normalize_flux(result["raw_flux"][idx])
    selected,selected_median=normalize_flux(result["selected_flux"][idx])
    standard,standard_median=normalize_flux(result["standard_flux"][idx])
    raw_error=result["raw_flux_err"][idx]/raw_median*1000
    t=time[idx]
    # These times follow eleanor's documented BTJD convention; no second barycentric correction.
    table=np.c_[t+2457000,t,raw,standard,selected,raw_error,result["quality"][idx]]
    np.savetxt(str(prefix)+"_lc.csv",table,delimiter=",",comments="",
               header="bjd_tdb,btjd,raw_flux_ppt,standard_flux_ppt,selected_flux_ppt,raw_flux_err_ppt,quality")
    frequency,power,raw_power,candidates,nyquist=calculate(t,raw,selected,cadence,args)
    np.savetxt(str(prefix)+"_lsp.csv",np.c_[frequency,frequency*.0864,power,raw_power],
               delimiter=",",comments="",header="frequency_uhz,frequency_cpd,selected_ls_power,raw_ls_power")
    write_csv(str(prefix)+"_candidates.csv",candidates,
               ["frequency_uhz","frequency_cpd","period_s","ls_power","single_frequency_amplitude_ppt","raw_single_frequency_amplitude_ppt","status"])
    plots(prefix,result,t,raw,selected,frequency,power,raw_power)
    stats={"sector":sector,"camera":result["camera"],"ccd":result["ccd"],
           "status":"extracted_and_analyzed","n_input":len(time),"n_used":len(t),
           "median_sampling_s":cadence,"nominal_sampling_nyquist_uhz":nyquist,
           "baseline_day":float(np.ptp(t)),"raw_normalization":raw_median,
           "standard_normalization":standard_median,"selected_normalization":selected_median,
           "time_convention":result["time_convention"],"correction":args.correction,
           "n_frequencies":len(frequency),"n_candidates":len(candidates),
           "aperture_weight_sum":float(np.sum(result["aperture"])),
           "fmin_uhz":float(frequency[0]),"fmax_uhz":float(frequency[-1]),
           "error_convention":"raw_flux_err only; not a corrected-light-curve covariance"}
    write_json(str(prefix)+"_metadata.json",stats)
    return stats


def run(args):
    label=f"TIC_{args.tic}" if args.tic is not None else f"RA_{args.ra:.7f}_DEC_{args.dec:.7f}"
    out=Path(args.output)/label;out.mkdir(parents=True,exist_ok=True)
    manifest={"started_utc":datetime.now(timezone.utc).isoformat(),"arguments":vars(args),
              "coverage_status":"not_queried","target":None,"coverage":[],"products":[],"errors":[],
              "versions":{}}
    for name in ["ffi-tess-compact","eleanor","astropy","astroquery","numpy","scipy"]:
        try:manifest["versions"][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:pass
    try:
        try:
            coords,target=target_coordinates(args);manifest["target"]=target
        except Exception as exc:
            manifest["coverage_status"]="target_resolution_failed"
            manifest["errors"].append({"stage":"target_resolution","error":str(exc)})
            print("Target resolution failed; FFI availability is UNKNOWN.")
            return 1
        try:coverage=discover(coords)
        except Exception as exc:
            manifest["coverage_status"]="query_failed_availability_unknown"
            manifest["errors"].append({"stage":"coverage_query","error":str(exc)})
            print("Archive query failed; this does NOT mean no FFI coverage.")
            return 1
        manifest["coverage"]=coverage
        manifest["coverage_status"]="coverage_found" if coverage else "no_coverage_returned"
        write_csv(out/"ffi_coverage.csv",coverage,["sector","camera","ccd"])
        if not coverage:
            print("No FFI footprint was returned for this position at query time.")
            return 0
        print("FFI coverage found (not yet an extraction guarantee):")
        for row in coverage:print(row)
        if not args.extract:return 0
        sectors=sorted(set(r["sector"] for r in coverage))
        requested=sectors if args.sectors is None else sorted(set(args.sectors))
        for sector in requested:
            matching=[r for r in coverage if r["sector"]==sector]
            if len(matching)!=1:
                message="Requested sector not returned" if not matching else "Multiple detectors cover sector; manual review needed"
                manifest["errors"].append({"stage":"sector_selection","sector":sector,"error":message})
                print(f"Sector {sector}: {message}");continue
            try:
                stats=process_sector(target,sector,matching[0],args,out)
                manifest["products"].append(stats)
                print(f"Sector {sector}: extracted and analyzed")
            except Exception as exc:
                manifest["errors"].append({"stage":"sector_extraction_or_analysis","sector":sector,
                                           "status":"coverage_found_extraction_or_analysis_failed","error":str(exc)})
                print(f"Sector {sector}: failed ({exc}); coverage remains positive")
        return 2 if manifest["errors"] else 0
    finally:
        manifest["finished_utc"]=datetime.now(timezone.utc).isoformat()
        write_json(out/"manifest.json",manifest)
