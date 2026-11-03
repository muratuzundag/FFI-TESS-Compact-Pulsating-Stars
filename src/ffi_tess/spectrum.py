"""Unweighted LS power plus diagnostic single-frequency amplitudes at candidates."""
import numpy as np

from .core import frequency_grid


def calculate(time, raw_ppt, selected_ppt, cadence, args):
    from astropy.timeseries import LombScargle
    from scipy.signal import find_peaks
    frequency,nyquist=frequency_grid(time,cadence,args.fmin,args.fmax,args.oversample,
                                     args.max_bins,args.super_nyquist)
    relative_time=(np.asarray(time)-time[0])*86400
    freq_hz=frequency*1e-6
    ls=LombScargle(relative_time,selected_ppt,fit_mean=True,center_data=True,nterms=1)
    power=ls.power(freq_hz,normalization="standard",method="fast")
    raw_ls=LombScargle(relative_time,raw_ppt,fit_mean=True,center_data=True,nterms=1)
    raw_power=raw_ls.power(freq_hz,normalization="standard",method="fast")
    if not np.all(np.isfinite(power)):raise ValueError("Invalid LS spectrum; check flux variation and grid")
    peaks,_=find_peaks(power,distance=max(1,args.oversample))
    # Candidates, not independently significant or prewhitened modes. Edges are excluded.
    chosen=sorted(peaks,key=lambda i:power[i],reverse=True)[:args.top_peaks]
    candidates=[]
    for i in chosen:
        theta=ls.model_parameters(freq_hz[i])
        amplitude=float(np.hypot(theta[1],theta[2]))
        raw_theta=raw_ls.model_parameters(freq_hz[i])
        raw_amplitude=float(np.hypot(raw_theta[1],raw_theta[2]))
        candidates.append({"frequency_uhz":float(frequency[i]),"frequency_cpd":float(frequency[i]*.0864),
                           "period_s":float(1/freq_hz[i]),"ls_power":float(power[i]),
                           "single_frequency_amplitude_ppt":amplitude,
                           "raw_single_frequency_amplitude_ppt":raw_amplitude,
                           "status":"candidate_only_not_significance_test"})
    return frequency,power,raw_power,candidates,nyquist
