"""FastAPI service: upload batch -> validate -> auto incident pipeline.

Run: uvicorn api.main:app --port 8000
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import agent_investigate, open_fix_mr, report, trigger
from src.validate import validate_batch

app = FastAPI(title="Pipeline Contract Agent", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "pipeline-contract-agent"}


@app.get("/contract")
def contract():
    from src.validate import load_contract
    from src import CONTRACT_PATH
    return load_contract(CONTRACT_PATH)


@app.post("/ingest")
async def ingest(file: UploadFile = File(...), auto_investigate: bool = True):
    suffix = Path(file.filename or "batch.csv").suffix or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    result = validate_batch(tmp_path)
    outcome = trigger.handle_result(Path(file.filename or "upload.csv"), result)
    # handle_result copies batch_path; tmp file has content but odd name — also stash real bytes
    payload: dict = {"filename": file.filename, "validation": result.to_dict(),
                     "status": outcome.status}
    if outcome.status == "quarantined":
        import shutil
        shutil.copy2(tmp_path, outcome.incident_dir / f"batch__{file.filename}")
        if auto_investigate:
            analysis = agent_investigate.enhance_with_llm(
                agent_investigate.analyse(result.to_dict()), result.to_dict())
            rp = report.write_report(outcome.incident_dir, file.filename,
                                     result.to_dict(), analysis)
            mr = open_fix_mr.propose(outcome.incident_dir, file.filename,
                                     result.to_dict(), analysis)
            payload["analysis"] = analysis
            payload["report"] = str(rp)
            payload["mr"] = mr
        payload["incident_dir"] = str(outcome.incident_dir)
        return JSONResponse(payload, status_code=422)
    return payload


@app.get("/incidents")
def incidents():
    from src import INCIDENTS_DIR
    if not INCIDENTS_DIR.exists():
        return {"incidents": []}
    return {"incidents": sorted(p.name for p in INCIDENTS_DIR.iterdir() if p.is_dir())}
