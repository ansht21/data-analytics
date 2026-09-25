"""LLM chat layer for the BI AI Agent.

- With GROQ_API_KEY present: a LangGraph ReAct agent (create_react_agent) with
  three guarded tools over the active DataFrame — get_data_info, filter_tool,
  analyze_data. Answers follow the consulting format:
  Finding -> Business explanation -> Actionable suggestion.
- Without a key (or on LLM error): a transparent offline mode that runs chip
  analytics + plain pandas summaries. A banner tells the viewer exactly which
  mode is active and what to set to unlock chat Q&A.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

import pandas as pd

AGENT_AVAILABLE = False
_agent_build_error = ""

try:  # optional — offline mode must work without these installed
    from dotenv import load_dotenv
    from langchain_core.tools import tool
    from langchain_groq import ChatGroq
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.prebuilt import create_react_agent

    AGENT_AVAILABLE = True
except Exception as exc:  # noqa: BLE001 — surfaced in the banner, not raised
    _agent_build_error = f"{type(exc).__name__}: {exc}"

SYSTEM_PROMPT = """You are a senior data analyst and business advisor. Help users explore
the loaded CSV/Excel dataset and answer business questions from it.

Tools:
1. get_data_info  - columns, dtypes, shape, preview (call first when unsure)
2. filter_tool    - filter rows with a pandas query condition
3. analyze_data   - run a pandas expression on the dataframe (called df)

Rules:
- Ground EVERY number in tool output. Never invent figures.
- Keep answers concise and business-friendly.
- Every answer has three parts:
  1. Finding & computed metric (exact numbers)
  2. Business explanation (why it matters / root cause)
  3. Decision / actionable suggestion (what management should do, or NOT do)
- If the data cannot answer a question, say so clearly.
"""


@dataclass
class ChatResult:
    answer: str
    mode: str  # "live" | "offline"
    detail: str = ""


def api_key_present() -> bool:
    try:
        from dotenv import load_dotenv as _load

        _load()
    except Exception:
        pass
    return bool(os.getenv("GROQ_API_KEY"))


def mode_banner() -> tuple[str, str]:
    """(banner_markdown, mode) for the sidebar status card."""
    if AGENT_AVAILABLE and api_key_present():
        return ("🟢 **Live AI chat enabled** (Groq + LangGraph ReAct agent).", "live")
    if not AGENT_AVAILABLE:
        return (
            "🟡 **Offline insight mode** — chat Q&A needs `pip install -r requirements.txt`. "
            f"Import detail: `{_agent_build_error}`",
            "offline",
        )
    return (
        "🟡 **Offline insight mode** — add `GROQ_API_KEY` to `.env` to unlock live AI chat Q&A. "
        "Quick-insight chips + executive brief work fully offline.",
        "offline",
    )


# ------------------------------------------------------------------ #
# Live agent (built lazily so module import never crashes Streamlit)
# ------------------------------------------------------------------ #
_DATAFRAME: pd.DataFrame | None = None
_AGENT = None
_THREAD_ID = str(uuid.uuid4())


def set_dataframe(df: pd.DataFrame) -> None:
    global _DATAFRAME
    _DATAFRAME = df


def _get_agent():
    """Build (once) the LangGraph ReAct agent bound to the current dataframe."""
    global _AGENT
    if _AGENT is not None:
        return _AGENT
    from dotenv import load_dotenv as _load
    from langchain_core.tools import tool
    from langchain_groq import ChatGroq
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.prebuilt import create_react_agent

    _load()

    @tool
    def get_data_info() -> str:
        """Columns, dtypes, shape and first five rows. Call first when unsure."""
        if _DATAFRAME is None:
            return "No dataset loaded."
        return (
            f"Shape: {_DATAFRAME.shape}\n\nColumns and dtypes:\n"
            f"{_DATAFRAME.dtypes.to_string()}\n\nFirst five rows:\n{_DATAFRAME.head().to_string()}"
        )

    @tool
    def filter_tool(condition: str) -> str:
        """Filter rows with a pandas query condition, e.g. "Hour >= 17 and Hour <= 19"."""
        if _DATAFRAME is None:
            return "No dataset loaded."
        try:
            result = _DATAFRAME.query(condition)
            return f"Found {len(result)} rows:\n{result.head(50).to_string()}"
        except Exception as e:  # noqa: BLE001 - surface to the LLM
            return f"Error: {e}"

    @tool
    def analyze_data(expression: str) -> str:
        """Run a pandas expression on df, e.g. df.groupby('Contract')['churned'].mean()."""
        if _DATAFRAME is None:
            return "No dataset loaded."
        try:
            df = _DATAFRAME  # noqa: F841 - visible to eval
            return str(eval(expression))  # noqa: S307 - local demo, errors surface to LLM
        except Exception as e:  # noqa: BLE001 - surface to the LLM
            return f"Error: {e}"

    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    _AGENT = create_react_agent(
        model=llm, tools=[get_data_info, filter_tool, analyze_data],
        prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver(),
    )
    return _AGENT


def chat(query: str) -> ChatResult:
    """Ask the live agent; on any failure return a transparent offline result."""
    if not (AGENT_AVAILABLE and api_key_present()):
        return ChatResult(
            answer=("Offline insight mode: live chat needs `GROQ_API_KEY` in `.env`. "
                    "Use the quick-insight chips or executive brief — they run fully offline."),
            mode="offline",
        )
    try:
        agent = _get_agent()
        response = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"configurable": {"thread_id": _THREAD_ID}},
        )
        return ChatResult(answer=response["messages"][-1].content, mode="live")
    except Exception as exc:  # noqa: BLE001 - never crash the UI
        return ChatResult(
            answer=f"⚠️ Live LLM call failed ({type(exc).__name__}: {exc}). "
                   "The numbers above the chat from quick-insight chips remain valid.",
            mode="offline", detail=str(exc),
        )

