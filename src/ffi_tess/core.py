"""Dependency-light validation, apertures, normalization, and sampling."""
import numpy as np


def validate_aperture(mask, shape):
    mask=np.asarray(mask,dtype=float)
    if mask.shape!=tuple(shape) or not np.all(np.isfinite(mask)):
        raise ValueError("Aperture must be finite and match the TPF (height, width)")
    if np.any(mask<0) or np.any(mask>1) or mask.sum()<=0:
        raise ValueError("Aperture weights must be in [0,1] with positive total weight")
    return mask


def circle_aperture(shape, x, y, radius):
    if not np.isfinite(radius) or radius<=0:
        raise ValueError("Aperture radius must be positive and finite")
    h,w=shape
    if not (np.isfinite(x) and np.isfinite(y) and 0<=x<w and 0<=y<h):
        raise ValueError("Target centroid is outside the TPF")
    if x-radius<-.5 or x+radius>w-.5 or y-radius<-.5 or y+radius>h-.5:
        raise ValueError("Aperture extends beyond TPF; enlarge stamp or reduce radius")
    yy,xx=np.indices(shape)
    return validate_aperture(((xx-x)**2+(yy-y)**2<=radius**2).astype(float),shape)


def cadence_seconds(time_day):
    finite=np.sort(np.asarray(time_day,dtype=float)[np.isfinite(time_day)])
    diffs=np.diff(finite);diffs=diffs[diffs>0]
    if len(diffs)<2:
        raise ValueError("Cannot estimate cadence from fewer than 3 distinct timestamps")
    return float(np.median(diffs)*86400)


def normalize_flux(flux):
    flux=np.asarray(flux,dtype=float)
    median=float(np.nanmedian(flux))
    if not np.isfinite(median) or median<=0:
        raise ValueError("Positive median flux required for relative normalization")
    return (flux/median-1)*1000,median


def clean_indices(time, raw, selected, quality, keep_flagged=False, sigma=None):
    t,r,y,q=[np.asarray(v) for v in (time,raw,selected,quality)]
    if not (t.ndim==r.ndim==y.ndim==q.ndim==1 and len(t)==len(r)==len(y)==len(q)):
        raise ValueError("Mismatched time/flux/quality arrays")
    mask=np.isfinite(t)&np.isfinite(r)&np.isfinite(y)&np.isfinite(q)
    if not keep_flagged:mask&=(q==0)
    idx=np.flatnonzero(mask);idx=idx[np.argsort(t[idx])]
    if sigma is not None:
        if not np.isfinite(sigma) or sigma<=0:raise ValueError("Invalid sigma clipping value")
        values=y[idx];med=np.median(values);scale=1.4826*np.median(np.abs(values-med))
        if scale>0:idx=idx[np.abs(values-med)<=sigma*scale]
    if len(idx)<20 or np.any(np.diff(t[idx])<=0):
        raise ValueError("Need >=20 valid, unique time samples; inspect flags and timestamps")
    return idx


def frequency_grid(time_day, cadence_s, fmin=None, fmax=None, oversample=5,
                   max_bins=1_000_000, super_nyquist=False):
    baseline=float(np.ptp(time_day))*86400
    if baseline<=0 or not np.isfinite(baseline) or cadence_s<=0 or not np.isfinite(cadence_s):
        raise ValueError("Invalid baseline or cadence")
    lo=1e6/baseline if fmin is None else fmin
    nyquist=1e6/(2*cadence_s)
    hi=.99*nyquist if fmax is None else fmax
    if not (np.isfinite(lo) and np.isfinite(hi) and 0<lo<hi):
        raise ValueError("Require finite 0 < fmin < fmax, in microhertz")
    if hi>nyquist and not super_nyquist:
        raise ValueError("Above cadence-based Nyquist; explicit --super-nyquist required")
    if oversample<1 or max_bins<2:raise ValueError("Invalid frequency grid settings")
    count=int(np.ceil((hi-lo)*1e-6*baseline*oversample))+1
    if count>max_bins:raise ValueError(f"Grid needs {count:,} bins; narrow range or increase --max-bins")
    return np.linspace(lo,hi,max(2,count)),nyquist
