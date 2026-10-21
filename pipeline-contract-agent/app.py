"""Operations dashboard: run batches, view violations, browse incidents.

Run: streamlit run app.py --server.port 8501
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.paths import INCIDENTS_DIR
from src.contract import contract_info
from src.paths import CONTRACT_PATH
from src.pipeline import run as run_pipeline

st.set_page_config(page_title="Pipeline Contract Agent", page_icon="🛡️", layout="wide")
st.title("🛡️ Pipeline Contract Agent — operations console")

info = contract_info(CONTRACT_PATH)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Contract", info["name"])
c2.metric("Version", info["version"])
c3.metric("Hash", info["sha256"])
c4.metric("Fields / rules", f"{info['fields']} / {info['rules']}")

st.divider()
st.subheader("▶ Run a batch")
col_a, col_b = st.columns(2)
with col_a:
    up = st.file_uploader("Upload raw batch CSV", type=["csv"])
    drift = st.selectbox("…or simulate drift on real data",
                         ["none", "dates", "nulls", "text", "mode", "all"])
    if st.button("Generate simulated batch"):
        r = subprocess.run([sys.executable, "src/ingest_sim.py", "--inject-drift", drift],
                           capture_output=True, text=True, cwd=ROOT)
        st.code(r.stdout or r.stderr)
with col_b:
    if up is not None:
        tmp = ROOT / "data" / f"upload_{up.name}"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(up.getvalue())
        if st.button("Validate + run pipeline"):
            with st.spinner("Running contract gate…"):
                out = run_pipeline(tmp, auto_investigate=True)
            if out["status"] == "passed":
                st.success(f"PASS — {out['validation']['total_rows']} rows loaded to warehouse.")
                st.json(out["warehouse"])
            else:
                st.error(f"QUARANTINED — {len(out['validation']['violations'])} rule(s) broken.")
                st.json(out["validation"]["violations"])
                st.markdown(f"**Report:** `{out['report']}`")
                st.json(out["mr"])

st.divider()
st.subheader("📁 Incident history")
if INCIDENTS_DIR.exists():
    incs = sorted((p for p in INCIDENTS_DIR.iterdir() if p.is_dir()),
                  key=lambda p: p.name, reverse=True)
    for inc in incs[:20]:
        with st.expander(f"🚨 {inc.name}"):
            for fname in ("validation.json", "manifest.json", "incident_report.md",
                          "mr_body.md", "fix.patch"):
                fp = inc / fname
                if fp.exists():
                    st.markdown(f"**{fname}**")
                    st.code(fp.read_text(encoding="utf-8")[:4000])
else:
    st.info("No incidents yet — run a drifted batch above.")
