"""
ICOT-RAG — research demo (Streamlit)

Run from project root:
  streamlit run streamlit_app.py
"""

from __future__ import annotations

import html
import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

EVAL_DIR = ROOT / "artifacts" / "evaluation"
DATASET = ROOT / "datasets" / "evaluation" / "iot_security_eval_v1.json"

st.set_page_config(
    page_title="ICOT-RAG",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design system — deep navy + amber gold on cool mist (premium contrast)
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
  --navy: #0b1d36;
  --navy-mid: #163158;
  --navy-soft: #e8eef6;
  --amber: #f0a202;
  --amber-deep: #d97706;
  --amber-soft: #fff4d6;
  --bg: #e9eef5;
  --bg-elevated: rgba(255, 255, 255, 0.88);
  --border: #c4d0de;
  --border-strong: #8fa3b8;
  --text: #0b1d36;
  --text-muted: #4d5f73;
  --radius: 10px;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: 'Manrope', system-ui, sans-serif !important;
  color: var(--text) !important;
  background-color: var(--bg) !important;
  background-image:
    radial-gradient(1000px 520px at -5% -10%, rgba(240, 162, 2, 0.14), transparent 55%),
    radial-gradient(900px 480px at 105% 0%, rgba(11, 29, 54, 0.12), transparent 52%),
    linear-gradient(165deg, #f4f7fb 0%, #e7edf5 45%, #dfe7f1 100%) !important;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }
.block-container {
  padding-top: 1.6rem !important;
  padding-bottom: 3rem !important;
  max-width: 1120px !important;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
  background:
    radial-gradient(420px 260px at 30% 0%, rgba(240, 162, 2, 0.16), transparent 65%),
    linear-gradient(185deg, #0b1d36 0%, #122846 48%, #081525 100%) !important;
  border-right: 1px solid #1e3a5f !important;
}
section[data-testid="stSidebar"] > div {
  background: transparent !important;
  padding-top: 1.35rem !important;
}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] small {
  color: #d7e3f2 !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
  color: #93a8c2 !important;
  opacity: 1 !important;
}
section[data-testid="stSidebar"] code {
  background: #1a3355 !important;
  color: #ffe08a !important;
  border-radius: 4px;
  padding: 0.1rem 0.35rem;
}

.sidebar-brand {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.03em;
  color: #fff8e7 !important;
  margin: 0 0 0.2rem 0 !important;
}
.sidebar-tagline {
  font-size: 0.82rem !important;
  color: #93a8c2 !important;
  margin: 0 0 0.9rem 0 !important;
  line-height: 1.4;
}
.status-row {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
  margin: 0.65rem 0 1.1rem 0;
}
.status-pill {
  display: inline-block;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.28rem 0.55rem;
  border-radius: 5px;
  background: rgba(240, 162, 2, 0.14);
  color: #ffd56a !important;
  border: 1px solid rgba(240, 162, 2, 0.35);
}

section[data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  background: transparent !important;
  color: #c5d6ea !important;
  border: 1px solid transparent !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding: 0.65rem 0.9rem !important;
  margin-bottom: 0.3rem !important;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255, 255, 255, 0.06) !important;
  border-color: #2a4a72 !important;
  color: #ffffff !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #f0a202 0%, #e8900a 100%) !important;
  color: #0b1d36 !important;
  border-color: #f0a202 !important;
  font-weight: 700 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] *,
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] * {
  color: #0b1d36 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"]:hover {
  background: linear-gradient(135deg, #ffb21a 0%, #f0a202 100%) !important;
  color: #0b1d36 !important;
}
section[data-testid="stSidebar"] hr {
  border-color: #234066 !important;
}

/* ---------- Typography (main only — do not paint over sidebar) ---------- */
[data-testid="stAppViewContainer"] > .main [data-testid="stMarkdownContainer"] p,
[data-testid="stAppViewContainer"] > .main [data-testid="stMarkdownContainer"] li,
[data-testid="stAppViewContainer"] > .main h1,
[data-testid="stAppViewContainer"] > .main h2,
[data-testid="stAppViewContainer"] > .main h3,
[data-testid="stAppViewContainer"] > .main h4 {
  color: var(--text) !important;
}
[data-testid="stAppViewContainer"] > .main .stCaption,
[data-testid="stAppViewContainer"] > .main [data-testid="stCaptionContainer"] {
  color: var(--text-muted) !important;
}

.page-eyebrow {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--amber-deep) !important;
  margin: 0 0 0.4rem 0 !important;
}
.page-title {
  font-family: 'Manrope', sans-serif !important;
  font-size: 2.1rem !important;
  font-weight: 800 !important;
  letter-spacing: -0.03em;
  color: var(--navy) !important;
  margin: 0 0 0.4rem 0 !important;
  line-height: 1.12 !important;
}
.page-lead {
  color: var(--text-muted) !important;
  font-size: 1.04rem !important;
  line-height: 1.55 !important;
  max-width: 40rem;
  margin: 0 0 1.4rem 0 !important;
}

.hero-brand {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: clamp(2.15rem, 4.4vw, 2.9rem) !important;
  font-weight: 600 !important;
  letter-spacing: -0.04em;
  background: linear-gradient(120deg, #0b1d36 20%, #1a4a7a 55%, #c47e00 110%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent !important;
  margin: 0 0 0.55rem 0 !important;
}
.hero-sub {
  color: var(--text-muted) !important;
  font-size: 1.1rem !important;
  line-height: 1.55 !important;
  max-width: 36rem;
  margin: 0 0 1.6rem 0 !important;
}

.section-label {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.68rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--navy-mid) !important;
  margin: 1.85rem 0 0.7rem 0 !important;
  padding-bottom: 0.45rem;
  border-bottom: 2px solid #d5e0ec;
}

/* ---------- KPI strip ---------- */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin: 0.35rem 0 1.6rem 0;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-elevated);
  overflow: hidden;
  box-shadow: 0 8px 28px rgba(11, 29, 54, 0.06);
}
@media (min-width: 900px) {
  .metric-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
.metric-card {
  padding: 1.1rem 1.15rem;
  border-right: 1px solid var(--border);
  background: transparent;
}
.metric-card:last-child { border-right: none; }
@media (max-width: 899px) {
  .metric-card:nth-child(2n) { border-right: none; }
  .metric-card:nth-child(-n+2) { border-bottom: 1px solid var(--border); }
}
.metric-label {
  color: var(--text-muted) !important;
  font-size: 0.7rem !important;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 700 !important;
}
.metric-value {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 1.18rem !important;
  color: var(--navy) !important;
  margin-top: 0.4rem !important;
  font-weight: 600 !important;
  line-height: 1.25;
}

/* ---------- Facets ---------- */
.chip-row { margin: 0.35rem 0 1rem 0; line-height: 2.15; }
.chip {
  display: inline-block;
  background: var(--navy-soft);
  color: var(--navy-mid) !important;
  border: 1px solid #b7c9de;
  border-radius: 5px;
  padding: 0.22rem 0.65rem;
  font-size: 0.8rem;
  margin: 0.12rem 0.28rem 0.12rem 0;
  font-family: 'IBM Plex Mono', monospace;
  font-weight: 600;
}
.chip-warn {
  background: var(--amber-soft);
  color: #92400e !important;
  border-color: #f5c45a;
}

/* ---------- Surfaces ---------- */
.panel {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.1rem 1.2rem;
  margin: 0.7rem 0 1.15rem 0;
  box-shadow: 0 6px 20px rgba(11, 29, 54, 0.05);
}
.panel-title {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.66rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted) !important;
  margin: 0 0 0.6rem 0 !important;
}
.answer-body {
  font-size: 1.02rem;
  line-height: 1.6;
  color: var(--text) !important;
}
.trace-box {
  background: #f7fafc;
  border: 1px solid var(--border);
  border-left: 4px solid var(--amber);
  padding: 0.85rem 1rem;
  margin: 0.5rem 0;
  border-radius: 0 8px 8px 0;
  color: var(--text) !important;
  line-height: 1.5;
}
.doc-line {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.76rem;
  color: var(--text-muted) !important;
  padding: 0.32rem 0;
  border-bottom: 1px solid #dce5ef;
}
.pipeline-step {
  display: grid;
  grid-template-columns: 2.4rem 1fr;
  gap: 0.8rem;
  align-items: start;
  padding: 0.9rem 0;
  border-bottom: 1px solid var(--border);
}
.pipeline-step:last-child { border-bottom: none; }
.step-num {
  font-family: 'IBM Plex Mono', monospace;
  font-weight: 600;
  font-size: 0.78rem;
  color: #0b1d36 !important;
  background: var(--amber);
  width: 2rem;
  height: 2rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.step-title {
  font-weight: 700 !important;
  color: var(--text) !important;
  margin: 0 0 0.2rem 0 !important;
}
.step-desc {
  font-size: 0.92rem !important;
  color: var(--text-muted) !important;
  margin: 0 !important;
  line-height: 1.45;
}
.takeaway {
  background: linear-gradient(120deg, #fff8e8 0%, #f3f7fc 100%);
  border: 1px solid #ecd79a;
  border-left: 4px solid var(--amber);
  border-radius: 0 8px 8px 0;
  padding: 0.95rem 1.15rem;
  margin: 0.75rem 0 1.25rem 0;
  color: var(--navy) !important;
  font-size: 0.97rem;
  line-height: 1.5;
}
.note-box {
  background: #fff4d6;
  border: 1px solid #f0c14d;
  border-left: 4px solid var(--amber-deep);
  border-radius: 0 8px 8px 0;
  padding: 0.85rem 1.1rem;
  margin: 0.75rem 0 1rem 0;
  color: #7c3d08 !important;
  font-size: 0.95rem;
  line-height: 1.45;
}

div[data-testid="stMetricValue"] {
  color: var(--navy) !important;
  font-family: 'IBM Plex Mono', monospace !important;
}
div[data-testid="stMetricLabel"] { color: var(--text-muted) !important; }

div[data-testid="stDataFrame"] {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

/* Primary CTA = amber */
.stApp .stButton > button[kind="primary"],
.stApp .stButton > button[data-testid="baseButton-primary"],
.stApp button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #f0a202 0%, #e08800 100%) !important;
  background-image: linear-gradient(135deg, #f0a202 0%, #e08800 100%) !important;
  color: #0b1d36 !important;
  border: 1px solid #e08800 !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  padding: 0.58rem 1.25rem !important;
}
.stApp .stButton > button[kind="primary"] *,
.stApp .stButton > button[data-testid="baseButton-primary"] * {
  color: #0b1d36 !important;
}
.stApp .stButton > button[kind="primary"]:hover,
.stApp .stButton > button[data-testid="baseButton-primary"]:hover {
  background: linear-gradient(135deg, #ffb41a 0%, #f0a202 100%) !important;
  border-color: #f0a202 !important;
  color: #0b1d36 !important;
}

.stTextArea textarea, .stTextInput input,
.stSelectbox div[data-baseweb="select"] > div {
  border-radius: 8px !important;
  border-color: var(--border-strong) !important;
}

hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ---------- Sidebar contrast FIX (last = wins over theme) ---------- */
section[data-testid="stSidebar"] .sidebar-brand,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] .sidebar-brand {
  color: #fff8e7 !important;
}
section[data-testid="stSidebar"] .sidebar-tagline,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] .sidebar-tagline,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {
  color: #c9d9ec !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] span {
  color: #a8bdd4 !important;
}
section[data-testid="stSidebar"] .status-pill {
  color: #ffd56a !important;
}
section[data-testid="stSidebar"] button,
section[data-testid="stSidebar"] button p,
section[data-testid="stSidebar"] button span,
section[data-testid="stSidebar"] button div,
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
section[data-testid="stSidebar"] [data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] [kind="secondary"] {
  color: #eef5ff !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"],
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-secondary"],
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(201, 217, 236, 0.35) !important;
  color: #eef5ff !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] *,
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-secondary"] *,
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] * {
  color: #eef5ff !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"],
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #f0a202 0%, #e8900a 100%) !important;
  border-color: #f0a202 !important;
  color: #0b1d36 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] *,
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] *,
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] * {
  color: #0b1d36 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_json(name: str) -> dict | list | None:
    path = EVAL_DIR / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_eval_questions() -> list[dict]:
    if not DATASET.exists():
        return []
    raw = json.loads(DATASET.read_text(encoding="utf-8"))
    items = raw["questions"] if isinstance(raw, dict) and "questions" in raw else raw
    return items


@st.cache_resource(show_spinner="Loading ICOT-RAG pipeline (embeddings + LLM)…")
def get_pipeline():
    from rag_icot.pipeline.rag_icot_pipeline import RAGICOTPipeline

    return RAGICOTPipeline()


def kb_document_count() -> str:
    """Live count from Chroma (fallback: master_documents.json)."""

    try:
        from chromadb import PersistentClient

        chroma_dir = ROOT / "artifacts" / "chroma_db"
        if chroma_dir.exists():
            col = PersistentClient(path=str(chroma_dir)).get_collection(
                "icot_knowledge"
            )
            return f"{col.count():,}"
    except Exception:
        pass

    master = ROOT / "artifacts" / "master_documents.json"
    if master.exists():
        try:
            return f"{len(json.loads(master.read_text(encoding='utf-8'))):,}"
        except Exception:
            pass
    return "—"


def page_header(eyebrow: str, title: str, lead: str) -> None:
    st.markdown(f'<p class="page-eyebrow">{eyebrow}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="page-title">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="page-lead">{lead}</p>', unsafe_allow_html=True)


def facet_chips(facets: list[str], warn: bool = False) -> str:
    cls = "chip chip-warn" if warn else "chip"
    return (
        '<div class="chip-row">'
        + "".join(
            f'<span class="{cls}">{html.escape(str(f))}</span>' for f in facets
        )
        + "</div>"
    )


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_overview():
    st.markdown('<p class="hero-brand">ICOT-RAG</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">Facet-aware iterative Chain-of-Thought RAG for IoT '
        "cybersecurity QA — multi-source retrieval, needed-facet stopping, and "
        "explainable traces over MITRE, VARIoT, and IoT-23.</p>",
        unsafe_allow_html=True,
    )

    metrics = [
        ("KB documents", kb_document_count()),
        ("Corpus", "MITRE · VARIoT · IoT-23"),
        ("Eval set", "50 questions"),
        ("Primary claim", "Facet@6 + faith ↑"),
    ]
    cards = "".join(
        f'<div class="metric-card"><div class="metric-label">{lab}</div>'
        f'<div class="metric-value">{val}</div></div>'
        for lab, val in metrics
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)

    st.markdown('<p class="section-label">Capability stack</p>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.markdown(
            """
- **Unified IoT security KB** — ATT&CK techniques/mitigations, VARIoT CVEs/exploits, IoT-23 malware behaviour  
- **Facet-aware ICOT** — multi-source first retrieve → check *needed* facets → targeted re-retrieve only on gaps  
- **Answer-context filtering** — facet-balanced set (≤6 docs) instead of dumping the full retrieve set  
"""
        )
    with col_b:
        st.markdown(
            """
- **Strong baselines** — vanilla RAG, prompt-only ICoT, ChatIoT-style multi-retriever  
- **Hard + soft metrics** — facet recall, facet@6, faithfulness, LLM-as-judge, human study  
- **Explainable trace** — thought, confidence, facets, next source, retrieved IDs per iteration  
"""
        )

    st.markdown('<p class="section-label">Evidence facets</p>', unsafe_allow_html=True)
    st.markdown(
        facet_chips(
            ["behaviour", "technique", "vulnerability", "exploit", "mitigation"]
        ),
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-label">Positioning</p>', unsafe_allow_html=True)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Work": "Zeng ICoT",
                    "Retrieval": "No",
                    "Iteration": "Prompt-only",
                    "Facet routing": "No",
                },
                {
                    "Work": "ChatIoT-style",
                    "Retrieval": "Multi-retriever (single pass)",
                    "Iteration": "No",
                    "Facet routing": "Per-source merge",
                },
                {
                    "Work": "This work (ICOT-RAG)",
                    "Retrieval": "Multi-source init + refine",
                    "Iteration": "Yes (if facets missing)",
                    "Facet routing": "Needed facets + filter + trace",
                },
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def page_demo():
    page_header(
        "Interactive",
        "Live demo",
        "Run the real facet-ICOT pipeline on eval samples or a custom question. "
        "Requires `.env` (`LLM_PROVIDER` + API key) and a built Chroma index.",
    )

    questions = load_eval_questions()
    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.markdown('<p class="section-label">Query</p>', unsafe_allow_html=True)
        categories = sorted({q.get("category", "general") for q in questions})
        cat_choice = st.selectbox(
            "Category",
            ["All"] + categories,
            help=f"{len(questions)} questions in the frozen eval set",
        )
        samples = [
            q
            for q in questions
            if cat_choice == "All" or q.get("category") == cat_choice
        ]
        labels = {
            f"{q['id']} [{q.get('category', '?')}]: "
            f"{q['question'][:72]}{'…' if len(q['question']) > 72 else ''}": q
            for q in samples
        }
        choice = st.selectbox(
            f"Sample ({len(samples)})",
            ["(custom)"] + list(labels.keys()),
        )
        if choice == "(custom)":
            question = st.text_area(
                "Question",
                value=(
                    "What network behaviours does Mirai show in the "
                    "IoT-23 Capture-7-1 scenario?"
                ),
                height=110,
            )
            required = None
        else:
            q = labels[choice]
            question = q["question"]
            required = q.get("required_facets")
            st.markdown(
                '<div class="panel"><p class="panel-title">Selected question</p>'
                f'<div class="answer-body">{html.escape(question)}</div></div>',
                unsafe_allow_html=True,
            )
            if required:
                st.caption("Required facets")
                st.markdown(facet_chips(required), unsafe_allow_html=True)

    with right:
        st.markdown('<p class="section-label">Controls</p>', unsafe_allow_html=True)
        iters = st.slider("Max ICOT iterations", 1, 3, 3)
        filter_ctx = st.checkbox("Answer-context filtering", value=True)
        st.caption("First run loads the embedding model once — expect a short wait.")
        run = st.button("Run facet ICOT", type="primary", use_container_width=True)

    if run:
        try:
            pipeline = get_pipeline()
            with st.spinner("Retrieving + reasoning…"):
                result = pipeline.run(
                    question,
                    max_iterations=iters,
                    required_facets=required,
                    filter_answer_context=filter_ctx,
                )
            st.session_state["last_result"] = result
            st.session_state["last_question"] = question
        except Exception as exc:
            st.error(f"Run failed: {type(exc).__name__}: {exc}")
            st.markdown(
                '<div class="note-box">Check <code>.env</code> '
                "(<code>LLM_PROVIDER=groq</code>, <code>GROQ_API_KEY=…</code>) "
                "and that Chroma exists under <code>artifacts/chroma_db</code>.</div>",
                unsafe_allow_html=True,
            )
            return

    result = st.session_state.get("last_result")
    if not result:
        st.markdown(
            '<div class="note-box">Pick a question and click <b>Run facet ICOT</b> '
            "to see the answer, filtered evidence, and iteration trace.</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown('<p class="section-label">Answer</p>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><p class="panel-title">System output</p></div>', unsafe_allow_html=True)
    st.markdown(result.get("answer") or "_(empty)_")

    c_cov, c_need = st.columns(2)
    with c_cov:
        covered = result.get("covered_facets") or []
        st.caption("Covered facets")
        if covered:
            st.markdown(facet_chips(covered), unsafe_allow_html=True)
        else:
            st.caption("—")
    with c_need:
        needed = result.get("needed_facets") or []
        st.caption("Needed facets")
        if needed:
            st.markdown(facet_chips(needed, warn=True), unsafe_allow_html=True)
        else:
            st.caption("Satisfied / not tracked")

    c1, c2 = st.columns(2, gap="large")
    docs = result.get("documents") or []
    adocs = result.get("answer_documents") or docs

    def _doc_lines(items: list[dict], include_detail: bool = True) -> str:
        lines = []
        for d in items:
            meta = d.get("metadata") or {}
            parts = [
                html.escape(str(d.get("id") or "")),
                html.escape(str(meta.get("source") or "")),
            ]
            if include_detail:
                detail = (
                    meta.get("document_type")
                    or meta.get("cve")
                    or meta.get("malware_family")
                    or ""
                )
                if detail:
                    parts.append(html.escape(str(detail)))
            lines.append(f'<div class="doc-line">{" · ".join(parts)}</div>')
        return "".join(lines) or '<div class="doc-line">—</div>'

    with c1:
        st.markdown(
            f'<div class="panel"><p class="panel-title">Retrieved '
            f"({len(docs)})</p>{_doc_lines(docs[:8])}</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="panel"><p class="panel-title">Answer context '
            f"({len(adocs)})</p>{_doc_lines(adocs, include_detail=False)}</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<p class="section-label">Explainable trace</p>', unsafe_allow_html=True)
    for step in result.get("trace") or []:
        stop = step.get("stop_reason")
        label = (
            f"Iteration {step.get('iteration')} · "
            f"confidence={step.get('confidence')} · "
            f"enough={step.get('enough_information')}"
        )
        if stop:
            label += f" · {stop}"
        with st.expander(label, expanded=step.get("iteration") == 1):
            thought = html.escape(str(step.get("thought") or ""))
            st.markdown(
                f'<div class="trace-box"><b>Thought</b><br/>{thought}</div>',
                unsafe_allow_html=True,
            )
            st.write("Reason:", step.get("reason"))
            if step.get("needed_facets"):
                st.write("Needed facets:", step.get("needed_facets"))
            st.write("Covered facets:", step.get("covered_facets"))
            st.write("Missing facets:", step.get("missing_facets"))
            st.write("Next source:", step.get("next_source"))
            st.write("Search query:", step.get("search_query"))
            st.write("Retrieved IDs:", step.get("retrieved_document_ids"))


def _hard_table_from_four_way(data: dict) -> pd.DataFrame:
    hard = data.get("hard_summary") or {}
    judge = data.get("judge_summary") or {}
    wins = data.get("judge_wins") or {}
    rows = []
    names = {
        "vanilla": "Vanilla RAG",
        "prompt_only_icot": "Prompt-only ICoT",
        "chatiot_style": "ChatIoT-style",
        "facet_icot": "Facet ICOT",
    }
    for key, label in names.items():
        h = hard.get(key) or {}
        j = judge.get(key) or {}
        rows.append(
            {
                "Method": label,
                "Facet recall": round(float(h.get("facet_recall", 0)), 3),
                "Facet@6": round(float(h.get("facet_recall_at_budget", 0)), 3),
                "Source hit": round(float(h.get("source_hit_rate", 0)), 3),
                "Keyword hit": round(float(h.get("keyword_hit_rate", 0)), 3),
                "Faithfulness": round(float(h.get("faithfulness_rate", 0)), 3),
                "Judge overall": round(float(j.get("overall", 0)), 3),
                "Judge wins": int(wins.get(key, 0)),
            }
        )
    return pd.DataFrame(rows)


def _hard_table_from_three_way(data: dict) -> pd.DataFrame:
    hard = data.get("hard_summary") or {}
    judge = data.get("judge_summary") or {}
    wins = data.get("judge_wins") or {}
    rows = []
    names = {
        "vanilla": "Vanilla RAG",
        "prompt_only_icot": "Prompt-only ICoT",
        "facet_icot": "Facet ICOT",
    }
    for key, label in names.items():
        h = hard.get(key) or {}
        j = judge.get(key) or {}
        rows.append(
            {
                "Method": label,
                "Facet recall": round(float(h.get("facet_recall", 0)), 3),
                "Source hit": round(float(h.get("source_hit_rate", 0)), 3),
                "Keyword hit": round(float(h.get("keyword_hit_rate", 0)), 3),
                "Judge overall": round(float(j.get("overall", 0)), 3),
                "Judge wins": int(wins.get(key, 0)),
            }
        )
    return pd.DataFrame(rows)


def _insight(title: str, body_html: str) -> None:
    st.markdown(
        f'<div class="takeaway"><b>{html.escape(title)}</b><br/>{body_html}</div>',
        unsafe_allow_html=True,
    )


def page_results():
    page_header(
        "Frozen evaluation",
        "Results",
        "Numbers from `artifacts/evaluation/full_four_way.json` "
        "(expanded KB + improved Facet ICOT), with interpretation of what each "
        "result means. See also `paper/results_draft.md`.",
    )

    with st.expander("What the metrics mean (read this first)", expanded=True):
        st.markdown(
            """
| Metric | What it measures | What a high score suggests |
|--------|------------------|----------------------------|
| **Facet recall** | Did retrieved docs cover the evidence types the question needs (behaviour, technique, CVE, exploit, mitigation)? | The system gathered the *kinds* of evidence required — not just similar text. |
| **Facet@6** | Same, but only using ≤6 docs (the answer-context budget). | Evidence is *compact* enough to fit the generator; less stuffing, better focus. |
| **Source hit** | Did we hit the right KB families (MITRE / VARIoT / IoT-23) when the gold expects them? | Routing across sources works, not only dense same-collection hits. |
| **Keyword hit** | Overlap with expected technical tokens (malware, CVE IDs, ATT&CK, etc.). | Surface-level topical match with the gold answer. |
| **Faithfulness** | Are cited CVE / ATT&CK-style IDs grounded in retrieved evidence (light automatic check)? | Fewer invented IDs; answers stay closer to the KB. |
| **Judge overall** | LLM-as-judge mean (reliability, relevance, technicality, friendliness). | How “good” the prose feels to another model — *not* the same as coverage. |
| **Judge wins** | How often that method had the best judge score on a question. | Preference count; ties are separate. |

**Important split:** hard metrics (facet / source / faith) answer *“did we get the right evidence?”*  
Judge scores answer *“does the written answer look strong?”* Those can diverge — and they do on this run.
"""
        )

    four = load_json("full_four_way.json")
    if four and four.get("hard_summary"):
        n = (four.get("hard_summary") or {}).get("n") or len(four.get("rows") or [])
        ties = four.get("judge_ties", "—")
        cfg = four.get("config") or {}

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Questions", str(n))
        m2.metric("Methods", "4")
        m3.metric("Judge ties", str(ties))
        m4.metric("Model", str(cfg.get("llm_model", "?"))[:18])

        st.markdown(
            f'<p class="section-label">Full 4-way comparison (n={n})</p>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"multisource_init={cfg.get('icot_multisource_init', '?')} · "
            f"answer-context filter on · max_iterations=3 · "
            f"generator={cfg.get('llm_model', '?')}"
        )
        df = _hard_table_from_four_way(four)
        st.dataframe(df, use_container_width=True, hide_index=True)

        chart_cols = [
            c
            for c in ["Facet recall", "Facet@6", "Faithfulness", "Judge overall"]
            if c in df.columns
        ]
        st.bar_chart(df.set_index("Method")[chart_cols], height=320)

        st.markdown(
            '<p class="section-label">Insights — what the full-set numbers suggest</p>',
            unsafe_allow_html=True,
        )
        _insight(
            "1. Retrieval alone is not enough — but reasoning without retrieval fails",
            "Prompt-only ICoT scores <b>0</b> on every hard metric and the lowest judge "
            "(~1.68). That tells us Zeng-style chain-of-thought <b>without a KB</b> cannot "
            "ground IoT cyber answers. Multi-source RAG is a necessary ingredient.",
        )
        _insight(
            "2. Facet ICOT wins the evidence story (coverage + budget + faithfulness)",
            "Facet ICOT leads <b>facet recall (1.00)</b>, <b>facet@6 (1.00)</b>, "
            "<b>source hit (1.00)</b>, and <b>faithfulness (~0.88)</b>. "
            "vs ChatIoT-style, the key gap is <b>facet@6 (1.00 vs 0.92)</b>: "
            "multi-source merge gets broad coverage, but ICOT’s needed-facet stop + "
            "≤6 filter keeps that coverage inside the answer budget. "
            "Higher faithfulness vs vanilla (~0.54) suggests fewer unsupported ID-like claims.",
        )
        _insight(
            "3. Vanilla still “sounds” better to the LLM judge — do not overclaim quality",
            "Vanilla has the highest mean judge (~3.42) and most wins (21). ChatIoT (~2.78) "
            "and Facet ICOT (~2.90) trail despite better evidence metrics. "
            "<b>What this suggests:</b> judges reward fluent, confident prose; denser or more "
            "cautious grounded answers can score lower even when evidence is stronger. "
            "Paper positioning should claim <b>grounded multi-facet completeness + faithfulness "
            "+ explainable traces</b>, not automatic dominance of answer style.",
        )
        _insight(
            "4. Practical takeaway for operators / SOC-style QA",
            "If the goal is “pull the right kinds of IoT evidence without flooding the "
            "context window,” Facet ICOT is the preferred design. If the goal is only "
            "“highest style score from an auto-judge,” vanilla remains competitive — "
            "which is why human ratings (faithfulness / usefulness / correctness) matter next.",
        )

        mf = (four.get("by_category") or {}).get("multi_facet")
        if mf:
            st.markdown(
                f'<p class="section-label">Multi-facet subset '
                f'(n={mf.get("n", "?")})</p>',
                unsafe_allow_html=True,
            )
            st.caption(
                "Questions that need ≥2 evidence facets (harder; closer to real analyst queries)."
            )
            mf_rows = []
            labels = {
                "vanilla": "Vanilla RAG",
                "prompt_only_icot": "Prompt-only ICoT",
                "chatiot_style": "ChatIoT-style",
                "facet_icot": "Facet ICOT",
            }
            hard = mf.get("hard") or {}
            judge_o = mf.get("judge_overall") or {}
            for key, label in labels.items():
                h = hard.get(key) or {}
                mf_rows.append(
                    {
                        "Method": label,
                        "Facet recall": round(float(h.get("facet_recall", 0)), 3),
                        "Facet@6": round(
                            float(h.get("facet_recall_at_budget", 0)), 3
                        ),
                        "Source hit": round(float(h.get("source_hit_rate", 0)), 3),
                        "Faithfulness": round(
                            float(h.get("faithfulness_rate", 0)), 3
                        ),
                        "Judge overall": round(float(judge_o.get(key, 0)), 3),
                    }
                )
            mf_df = pd.DataFrame(mf_rows)
            st.dataframe(mf_df, use_container_width=True, hide_index=True)

            st.markdown(
                '<p class="section-label">Insights — multi-facet subset</p>',
                unsafe_allow_html=True,
            )
            _insight(
                "5. Hard questions expose vanilla’s weakness",
                "Vanilla facet recall drops to ~<b>0.69</b> when several facets are required. "
                "Single-pass retrieve often cannot cover behaviour + technique + CVE/mitigation "
                "together. ChatIoT and Facet ICOT both reach <b>1.00</b> facet / source — "
                "multi-source retrieval is the fix.",
            )
            _insight(
                "6. Facet@6 is where ICOT pulls ahead of ChatIoT-style",
                "Both multi-source systems cover facets in the full pool, but ChatIoT "
                "facet@6 falls to ~<b>0.86</b> while Facet ICOT stays at <b>1.00</b>. "
                "<b>Suggestion:</b> merging many docs is not enough; selecting a "
                "facet-balanced ≤6 set for generation preserves what the question needs "
                "under a realistic context budget.",
            )
            _insight(
                "7. On multi-facet items, judge flips toward Facet ICOT",
                "Facet ICOT leads mean judge (~<b>3.48</b>) vs vanilla (~3.38) and ChatIoT "
                "(~3.08) on this subset. That suggests the method’s value shows most when "
                "questions are <b>evidence-compositional</b> — exactly the setting the "
                "architecture targets. Full-set judge leadership of vanilla is partly driven "
                "by easier single-facet questions.",
            )
    else:
        st.warning("Missing or incomplete `full_four_way.json`")

    ab = load_json("llm_iter_ablation_multifacet.json") or load_json(
        "llm_iter_ablation.json"
    )
    if ab and ab.get("summary"):
        st.markdown(
            '<p class="section-label">Ablation — iteration budget</p>',
            unsafe_allow_html=True,
        )
        rows = []
        for k, v in ab["summary"].items():
            rows.append(
                {
                    "Condition": k,
                    "Facet recall": round(v.get("facet_recall", 0), 3),
                    "Source hit": round(v.get("source_hit_rate", 0), 3),
                    "Judge": round(v.get("judge_overall", 0), 3),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        _insight(
            "8. Extra iterations are often idle after multi-source init",
            "On the multi-facet ablation, iter=1 and iter=3 look similar on hard metrics. "
            "With multi-source first retrieve, needed facets are frequently covered on the "
            "first pass, so the loop mostly <b>checks sufficiency and stops</b>. "
            "Iterations still matter as a safety net when gaps remain — cost stays low "
            "when coverage is already good.",
        )

    filt = load_json("answer_context_filter_multifacet.json") or load_json(
        "answer_context_filter_compare.json"
    )
    if filt and filt.get("summary"):
        st.markdown(
            '<p class="section-label">Ablation — answer-context filter</p>',
            unsafe_allow_html=True,
        )
        s = filt["summary"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Full-context judge", f"{s.get('avg_full_context', 0):.2f}")
        c2.metric("Filtered judge", f"{s.get('avg_filtered', 0):.2f}")
        c3.metric("Delta", f"{s.get('delta', 0):+.2f}")
        _insight(
            "9. Filtering trades length for focus",
            "Compare full retrieved context vs a facet-balanced ≤6 set. A small judge "
            "delta (positive or negative) still supports filtering as an engineering "
            "choice: less noise, clearer grounding, controllable token cost — "
            "aligned with the facet@6 gains on the main table.",
        )

    st.markdown(
        '<p class="section-label">Bottom line for the paper / demo</p>',
        unsafe_allow_html=True,
    )
    _insight(
        "What we claim",
        "Facet-aware ICOT-RAG improves <b>multi-source / multi-facet evidence completeness</b>, "
        "<b>budgeted coverage (facet@6)</b>, and <b>faithfulness</b> vs vanilla and ChatIoT-style, "
        "and clearly beats prompt-only ICoT. Benefit is largest on multi-facet questions.",
    )
    _insight(
        "What we do not claim",
        "We do <b>not</b> claim full-set mean LLM-judge dominance — vanilla often wins style. "
        "Human evaluation (in progress) is needed to validate faithfulness / usefulness "
        "beyond auto-judge.",
    )

    st.markdown(
        '<p class="section-label">Per-question judge (4-way)</p>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Scan for patterns: vanilla wins are common on single-facet rows; "
        "Facet ICOT / ChatIoT compete more on multi_facet categories."
    )
    if four and four.get("rows"):
        detail = []
        for r in four["rows"]:
            j = r.get("judges") or {}
            detail.append(
                {
                    "ID": r["id"],
                    "Category": r.get("category", ""),
                    "Vanilla": round(j.get("vanilla", {}).get("overall", 0), 2),
                    "Prompt-only": round(
                        j.get("prompt_only_icot", {}).get("overall", 0), 2
                    ),
                    "ChatIoT-style": round(
                        j.get("chatiot_style", {}).get("overall", 0), 2
                    ),
                    "Facet ICOT": round(j.get("facet_icot", {}).get("overall", 0), 2),
                }
            )
        st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True)

    with st.expander("Historical — older 3-way multi-facet (n=12)"):
        st.caption(
            "Pre-improvement artifact (no ChatIoT-style). Kept for lineage only — "
            "prefer full_four_way.json for claims."
        )
        three = load_json("multifacet_three_way.json")
        if three:
            st.dataframe(
                _hard_table_from_three_way(three),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No multifacet_three_way.json found.")


def page_howto():
    page_header(
        "Architecture",
        "How it works",
        "Needed facets drive when to stop and which source to query next — "
        "not a fixed full pass over every facet every time.",
    )

    steps = [
        ("01", "Infer needed facets", "Map the question to behaviour, technique, vulnerability, exploit, and/or mitigation."),
        ("02", "Multi-source retrieve", "First pass pulls from IoT-23, MITRE, and VARIoT in parallel, then merges."),
        ("03", "ICOT loop (max 3)", "If needed facets are covered → stop. Else reason a gap and re-retrieve that source."),
        ("04", "Filter answer context", "Keep a facet-balanced set of ≤6 docs for generation."),
        ("05", "Generate + trace", "Grounded IoT security report plus iteration thought, facets, and retrieved IDs."),
    ]
    step_html = "".join(
        f'<div class="pipeline-step">'
        f'<div class="step-num">{num}</div>'
        f"<div><p class=\"step-title\">{title}</p>"
        f'<p class="step-desc">{desc}</p></div></div>'
        for num, title, desc in steps
    )
    st.markdown(f'<div class="panel">{step_html}</div>', unsafe_allow_html=True)

    st.markdown('<p class="section-label">Repository map</p>', unsafe_allow_html=True)
    st.code(
        """rag_icot/              # core library
  pipeline/            # RAGICOTPipeline
  components/          # retriever, reasoner, filter, prompt-only ICoT
  evaluation/          # baselines, metrics, judge
artifacts/evaluation/  # frozen JSONs (full_four_way.json)
paper/                 # results_draft.md, methods_draft.md
streamlit_app.py       # this demo""",
        language="text",
    )

    st.markdown(
        '<div class="takeaway"><b>Paper claim alignment.</b> Emphasize budgeted facet '
        "coverage and faithfulness. Prompt-only ICoT is not enough; vanilla may still "
        "win mean judge on the full set — disclose that honestly.</div>",
        unsafe_allow_html=True,
    )


def main():
    pages = [
        ("Overview", "overview"),
        ("Live demo", "demo"),
        ("Results", "results"),
        ("How it works", "howto"),
    ]
    if "page" not in st.session_state:
        st.session_state.page = "Overview"

    with st.sidebar:
        st.markdown('<p class="sidebar-brand">ICOT-RAG</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sidebar-tagline">IoT cybersecurity research demo</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="status-row">'
            '<span class="status-pill">MITRE</span>'
            '<span class="status-pill">VARIoT</span>'
            '<span class="status-pill">IoT-23</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        for name, _ in pages:
            active = st.session_state.page == name
            if st.button(
                name,
                key=f"nav_{name}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.page = name
                st.rerun()

        st.divider()
        st.caption(f"KB · {kb_document_count()} docs")
        st.caption("Package · `rag_icot`")
        st.caption("LLM · `.env` → Groq / Gemini")

    page = st.session_state.page
    if page == "Overview":
        page_overview()
    elif page == "Live demo":
        page_demo()
    elif page == "Results":
        page_results()
    else:
        page_howto()


if __name__ == "__main__":
    main()
