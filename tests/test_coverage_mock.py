"""Distinct availability statuses under mocked archive conditions."""
import json
from types import SimpleNamespace
import pytest

import ffi_tess.pipeline as pipeline
from ffi_tess.cli import parser


def args(tmp_path,extra=None):
    return parser().parse_args(["--tic","123","--output",str(tmp_path),*(extra or [])])


def manifest(tmp_path):
    return json.loads((tmp_path/"TIC_123"/"manifest.json").read_text())


def test_no_coverage(tmp_path,monkeypatch):
    monkeypatch.setattr(pipeline,"target_coordinates",lambda a:(None,{"tic":123}))
    monkeypatch.setattr(pipeline,"discover",lambda c:[])
    assert pipeline.run(args(tmp_path))==0
    assert manifest(tmp_path)["coverage_status"]=="no_coverage_returned"


def test_query_failure_not_no_coverage(tmp_path,monkeypatch):
    monkeypatch.setattr(pipeline,"target_coordinates",lambda a:(None,{"tic":123}))
    def fail(c):raise RuntimeError("Service unavailable")
    monkeypatch.setattr(pipeline,"discover",fail)
    assert pipeline.run(args(tmp_path))==1
    assert manifest(tmp_path)["coverage_status"]=="query_failed_availability_unknown"


def test_all_sectors_attempted_and_failure_recorded(tmp_path,monkeypatch):
    monkeypatch.setattr(pipeline,"target_coordinates",lambda a:(None,{"tic":123}))
    monkeypatch.setattr(pipeline,"discover",lambda c:[{"sector":1,"camera":1,"ccd":1},
                                                     {"sector":2,"camera":1,"ccd":2}])
    attempted=[]
    def process(target,sector,*other):
        attempted.append(sector)
        if sector==2:raise RuntimeError("Download failed")
        return {"sector":sector,"status":"extracted_and_analyzed"}
    monkeypatch.setattr(pipeline,"process_sector",process)
    assert pipeline.run(args(tmp_path,["--extract"]))==2
    assert attempted==[1,2]
    result=manifest(tmp_path)
    assert result["coverage_status"]=="coverage_found" and len(result["products"])==1
