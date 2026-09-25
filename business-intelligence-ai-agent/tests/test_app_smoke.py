"""Headless UI smoke test — runs the real app.py with a stubbed streamlit.

No streamlit/plotly install needed: the stub records UI calls while the real
pandas loaders, KPIs and offline agent path execute against the real CSVs.
"""
from __future__ import annotations

import sys
import types


class FakeSessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class _Ctx:
    def __init__(self, fake):
        self.fake = fake

    def __enter__(self):
        return self.fake

    def __exit__(self, *args):
        return False


class _Col:
    def __init__(self, fake):
        self.fake = fake

    def metric(self, *args, **kwargs):
        self.fake.calls.append(("metric", args, kwargs))


def _make_fake_streamlit():
    fake = types.ModuleType("streamlit")
    fake.calls = []
    fake.session_state = FakeSessionState()
    fake.sidebar = _Ctx(fake)

    def _rec(name):
        def _fn(*args, **kwargs):
            fake.calls.append((name, args, kwargs))
            return None
        return _fn

    for name in ("set_page_config", "header", "divider", "info", "caption", "title",
                 "dataframe", "subheader", "write", "markdown", "code",
                 "plotly_chart", "download_button", "warning"):
        setattr(fake, name, _rec(name))

    def radio(label, options, index=0, **kwargs):
        fake.calls.append(("radio", (label,), {"options": options}))
        return options[index]

    def file_uploader(*args, **kwargs):
        fake.calls.append(("file_uploader", args, kwargs))
        return None

    def button(*args, **kwargs):
        fake.calls.append(("button", args, kwargs))
        return False

    def chat_input(*args, **kwargs):
        fake.calls.append(("chat_input", args, kwargs))
        return None

    def columns(n, **kwargs):
        fake.calls.append(("columns", (n,), kwargs))
        return [_Col(fake) for _ in range(n)]

    def cache_data(*dargs, **dkwargs):
        def deco(func):
            return func
        return deco

    def spinner(*args, **kwargs):
        fake.calls.append(("spinner", args, kwargs))
        return _Ctx(fake)

    def chat_message(*args, **kwargs):
        fake.calls.append(("chat_message", args, kwargs))
        return _Ctx(fake)

    def expander(*args, **kwargs):
        fake.calls.append(("expander", args, kwargs))
        return _Ctx(fake)

    def stop():
        raise RuntimeError("st.stop() called")

    fake.radio, fake.file_uploader, fake.button = radio, file_uploader, button
    fake.chat_input, fake.columns, fake.cache_data = chat_input, columns, cache_data
    fake.spinner, fake.chat_message, fake.expander, fake.stop = spinner, chat_message, expander, stop
    return fake


def test_app_runs_offline_end_to_end():
    fake = _make_fake_streamlit()
    sys.modules["streamlit"] = fake
    sys.modules.pop("app", None)
    import app as app_module  # noqa: F401 — executes the whole UI script

    assert fake.session_state["dataset_key"] == "supply"
    metrics = [c for c in fake.calls if c[0] == "metric"]
    assert len(metrics) == 4, f"expected 4 KPI cards, got {len(metrics)}"
    values = [str(m[1][1]) for m in metrics]
    assert any(v.startswith("$73.") for v in values), values
    buttons = [str(b[1][0]) for b in fake.calls if b[0] == "button"]
    assert any("Warehouse Trap Check" in b for b in buttons), buttons
    assert any("Generate Executive Brief" in b for b in buttons), buttons
    assert any(c[0] == "dataframe" for c in fake.calls)
    assert any(c[0] == "chat_input" for c in fake.calls)
