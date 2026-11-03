"""Thin, explicit adapter to separately installed eleanor; no vendored source."""
import numpy as np

from .core import circle_aperture, validate_aperture


def extract(target, sector, args):
    try:
        import eleanor
    except ImportError as exc:
        raise RuntimeError('Install extraction dependencies: python -m pip install ".[extract]"') from exc
    source_kwargs={"sector":sector,"tc":True,"tesscut_size":args.cutout_size}
    if target["tic"] is not None:source_kwargs["tic"]=int(target["tic"])
    source_kwargs["coords"]=(target["ra_deg"],target["dec_deg"])
    star=eleanor.Source(**source_kwargs)
    if int(star.sector)!=sector:raise ValueError("eleanor returned the wrong sector")
    data=eleanor.TargetData(star,height=args.height,width=args.width,bkg_size=args.background_size,
                            do_psf=False,do_pca=False,try_load=False,aperture_mode=args.aperture_mode)
    shape=np.shape(data.tpf)[1:]
    if args.aperture=="circle":
        x=float(data.tpf_star_x) if args.center is None else args.center[0]
        y=float(data.tpf_star_y) if args.center is None else args.center[1]
        aperture=circle_aperture(shape,x,y,args.radius)
    elif args.aperture=="mask":
        aperture=validate_aperture(np.load(args.mask,allow_pickle=False),shape)
    else:aperture=validate_aperture(data.aperture,shape)
    if args.aperture!="auto":data.get_lightcurve(aperture=aperture)
    aperture=validate_aperture(data.aperture,shape)
    raw=np.asarray(data.raw_flux,dtype=float).copy()
    # Explicitly recompute for the selected aperture; do not reuse pre-aperture corrections.
    standard=np.asarray(data.corrected_flux(flux=raw,pca=False),dtype=float).copy()
    data.corr_flux=standard
    pca=np.full_like(raw,np.nan)
    if args.correction=="pca":
        pca=np.asarray(data.corrected_flux(flux=raw,pca=True,modes=args.pca_modes),dtype=float).copy()
    selected={"standard":standard,"pca":pca,"none":raw}[args.correction]
    # eleanor flux_err is explicitly a RAW-aperture uncertainty, not a corrected covariance.
    raw_error=np.asarray(getattr(data,"flux_err",np.full_like(raw,np.nan)),dtype=float)
    if raw_error.shape!=raw.shape:raise ValueError("Invalid eleanor flux_err shape")
    return {"time_btjd":np.asarray(data.time,dtype=float),"raw_flux":raw,
            "standard_flux":standard,"pca_flux":pca,"selected_flux":selected,
            "raw_flux_err":raw_error,"quality":np.asarray(data.quality),
            "aperture":aperture,"median_image":np.nanmedian(data.tpf,axis=0),
            "camera":int(star.camera),"ccd":int(star.chip),
            "source_sector":int(star.sector),"time_convention":"eleanor BTJD; BJD_TDB=BTJD+2457000"}
