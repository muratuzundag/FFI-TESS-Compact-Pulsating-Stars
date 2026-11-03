import numpy as np
import pytest

from ffi_tess.core import (cadence_seconds,circle_aperture,validate_aperture,
                           normalize_flux,clean_indices,frequency_grid)
from ffi_tess.cli import main,parser


def test_circle():
    mask=circle_aperture((15,15),7,7,1.5)
    assert mask.shape==(15,15) and mask.sum()==9 and mask[7,7]==1


@pytest.mark.parametrize("mask",[np.zeros((3,3)),np.ones((2,2)),np.full((3,3),2),np.full((3,3),np.nan)])
def test_invalid_masks(mask):
    with pytest.raises(ValueError):validate_aperture(mask,(3,3))


def test_aperture_edge():
    with pytest.raises(ValueError):circle_aperture((5,5),0,0,2)


def test_normalization():
    y,median=normalize_flux([99.,100.,101.])
    assert median==100 and np.allclose(y,[-10,0,10])


def test_bad_median():
    with pytest.raises(ValueError):normalize_flux([-1.,-2.])


@pytest.mark.parametrize("cadence",[1800,600,200])
def test_cadence_and_nyquist(cadence):
    time=np.arange(100)*cadence/86400
    measured=cadence_seconds(time)
    assert measured==pytest.approx(cadence)
    f,ny=frequency_grid(time,measured)
    assert ny==pytest.approx(1e6/(2*cadence)) and f[-1]<ny


def test_quality_mask():
    t=np.arange(30.);q=np.zeros(30);q[2]=1
    idx=clean_indices(t,np.ones(30),np.ones(30),q)
    assert 2 not in idx and len(idx)==29
    assert len(clean_indices(t,np.ones(30),np.ones(30),q,True))==30


def test_duplicate_times():
    t=np.arange(30.);t[2]=t[1]
    with pytest.raises(ValueError):clean_indices(t,np.ones(30),np.ones(30),np.zeros(30))


def test_grid_guard():
    with pytest.raises(ValueError):frequency_grid([0,1000],200,max_bins=10)


def test_supernyquist_guard():
    with pytest.raises(ValueError):frequency_grid([0,20],1800,1,1000)
    assert frequency_grid([0,20],1800,1,1000,super_nyquist=True)[0][-1]==1000


def test_inventory_default():
    args=parser().parse_args(["--tic","123"])
    assert not args.extract and args.aperture=="circle" and args.correction=="standard"


@pytest.mark.parametrize("args",[
    ["--tic","-1"], ["--ra","500","--dec","2"], ["--ra","20"],
    ["--tic","1","--dec","2"], ["--tic","1","--height","8"],
    ["--tic","1","--aperture","mask"], ["--tic","1","--radius","0"],
    ["--tic","1","--sigma","nan"], ["--tic","1","--fmin","10","--fmax","5"],
])
def test_invalid_cli(args):
    with pytest.raises(SystemExit) as exc:main(args)
    assert exc.value.code==2
