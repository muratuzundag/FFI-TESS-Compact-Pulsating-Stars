"""Command-line interface; inventory is the safe default."""
import argparse
import math

from . import __version__


def parser():
    p=argparse.ArgumentParser(description="FFI TESS Compact pulsating stars: coverage, eleanor and LS")
    target=p.add_mutually_exclusive_group(required=True)
    target.add_argument("--tic",type=int)
    target.add_argument("--ra",type=float,help="ICRS decimal-degree right ascension")
    p.add_argument("--dec",type=float)
    p.add_argument("--extract",action="store_true",help="Default is coverage inventory only")
    p.add_argument("--sectors",nargs="+",type=int,help="Default: all coverage sectors")
    p.add_argument("--aperture",choices=["circle","mask","auto"],default="circle")
    p.add_argument("--radius",type=float,default=1.5,help="Circular aperture radius in TESS pixels")
    p.add_argument("--center",nargs=2,type=float,metavar=("X","Y"),help="Optional TPF zero-based pixel coordinates")
    p.add_argument("--mask",help="2-D .npy aperture with weights in [0,1]")
    p.add_argument("--height",type=int,default=15)
    p.add_argument("--width",type=int,default=15)
    p.add_argument("--cutout-size",type=int,default=31)
    p.add_argument("--background-size",type=int,default=31)
    p.add_argument("--aperture-mode",choices=["normal","small","large","all"],default="normal")
    p.add_argument("--correction",choices=["standard","pca","none"],default="standard")
    p.add_argument("--pca-modes",type=int,default=3)
    p.add_argument("--keep-flagged",action="store_true",help="Default: only eleanor quality == 0")
    p.add_argument("--sigma",type=float,help="Optional one-pass MAD clipping; off by default")
    p.add_argument("--fmin",type=float,help="Microhertz, default 1/baseline")
    p.add_argument("--fmax",type=float,help="Microhertz, default 0.99 cadence-based Nyquist")
    p.add_argument("--oversample",type=int,default=5)
    p.add_argument("--max-bins",type=int,default=1000000)
    p.add_argument("--super-nyquist",action="store_true")
    p.add_argument("--top-peaks",type=int,default=10)
    p.add_argument("--output",default="results")
    p.add_argument("--version",action="version",version=__version__)
    return p


def validate(p,a):
    if (a.ra is None)!=(a.dec is None):p.error("Supply --ra and --dec together, or --tic")
    if a.tic is not None and a.tic<=0:p.error("TIC must be positive")
    if a.ra is not None and not (math.isfinite(a.ra) and math.isfinite(a.dec)
                                 and 0<=a.ra<360 and -90<=a.dec<=90):p.error("Invalid ICRS coordinates")
    for name in ["radius","sigma","fmin","fmax"]:
        v=getattr(a,name)
        if v is not None and (not math.isfinite(v) or v<=0):p.error(f"{name} must be positive and finite")
    if a.fmin is not None and a.fmax is not None and a.fmin>=a.fmax:p.error("Require fmin < fmax")
    if a.aperture=="mask" and not a.mask:p.error("--aperture mask requires --mask")
    if a.mask and a.aperture!="mask":p.error("Use --aperture mask with --mask")
    if a.center and (a.aperture!="circle" or not all(math.isfinite(v) for v in a.center)):
        p.error("--center requires a circular aperture and finite coordinates")
    for name in ["height","width","cutout_size","background_size"]:
        v=getattr(a,name)
        if v<3 or v%2==0:p.error(f"{name} must be odd and >=3")
    if a.cutout_size<max(a.height,a.width,a.background_size):p.error("Cutout must contain stamp and background box")
    if a.sectors and any(s<1 for s in a.sectors):p.error("Sectors must be positive")
    if min(a.oversample,a.pca_modes,a.top_peaks)<1 or a.max_bins<2:p.error("Invalid grid/PCA/peak count")


def main(argv=None):
    p=parser();a=p.parse_args(argv);validate(p,a)
    try:
        from .pipeline import run
        return run(a)
    except Exception as exc:
        print(f"FFI-TESS failed: {exc}")
        return 1
