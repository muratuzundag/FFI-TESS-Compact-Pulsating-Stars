"""Mocked API contract, NOT a validation against installed eleanor or TESS data."""
from types import SimpleNamespace
import sys
import numpy as np

from ffi_tess.cli import parser
from ffi_tess.eleanor_adapter import extract


def test_custom_aperture_correction_recomputed(monkeypatch):
    calls=[]
    class Source:
        def __init__(self,**kwargs):
            assert kwargs["tc"] is True
            self.sector=kwargs["sector"];self.camera=1;self.chip=2
    class TargetData:
        def __init__(self,*args,**kwargs):
            self.tpf=np.ones((30,15,15));self.tpf_star_x=7;self.tpf_star_y=7
            self.raw_flux=np.full(30,100.);self.quality=np.zeros(30)
            self.time=np.arange(30)*200/86400+2000
            self.flux_err=np.ones(30);self.aperture=np.ones((15,15))
        def get_lightcurve(self,aperture):
            self.aperture=aperture;self.raw_flux=np.full(30,aperture.sum()*100.)
        def corrected_flux(self,flux,pca=False,**kwargs):
            calls.append((flux.copy(),pca));return flux+1
    monkeypatch.setitem(sys.modules,"eleanor",SimpleNamespace(Source=Source,TargetData=TargetData))
    args=parser().parse_args(["--tic","123","--extract"])
    result=extract({"tic":123,"ra_deg":10,"dec_deg":5},1,args)
    assert np.all(calls[0][0]==900)
    assert np.all(result["selected_flux"]==901)
    assert result["aperture"].sum()==9
