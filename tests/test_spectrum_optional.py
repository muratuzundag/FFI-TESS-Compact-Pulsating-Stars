"""Analytical unit fixture, NOT observed photometry or a variability claim."""
from types import SimpleNamespace
import numpy as np
import pytest

pytest.importorskip("astropy")
from ffi_tess.spectrum import calculate


def test_frequency_and_amplitude():
    t=np.arange(3000)*200/86400
    # A noise-free test signal with known 2-ppt amplitude below cadence Nyquist.
    y=2*np.sin(2*np.pi*100e-6*t*86400)
    a=SimpleNamespace(fmin=50,fmax=150,oversample=10,max_bins=100000,
                      super_nyquist=False,top_peaks=3)
    f,p,r,candidates,ny=calculate(t,y,y,200,a)
    assert candidates[0]["frequency_uhz"]==pytest.approx(100,abs=.5)
    assert candidates[0]["single_frequency_amplitude_ppt"]==pytest.approx(2,rel=.02)
    assert np.allclose(p,r)
