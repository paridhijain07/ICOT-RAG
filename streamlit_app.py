"""
ICOT-RAG — Professor demo (Streamlit)

Run from project root:
  streamlit run streamlit_app.py
"""

from __future__ import annotations

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
    page_title="ICOT-RAG Demo",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Light UI only: dark text on light surfaces (WCAG contrast) ---
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: 'DM Sans', sans-serif !important;
  color: #15202b !important;
  background: #f4f7f9 !important;
}

/* Sidebar: SAME light surface as main — never dark-on-dark */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
  background: #e8eef2 !important;
  border-right: 1px solid #c5d0db !important;
}
section[data-testid="stSidebar"] * {
  color: #15202b !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
  color: #15202b !important;
  opacity: 1 !important;
  visibility: visible !important;
}
section[data-testid="stSidebar"] code {
  background: #d5dee8 !important;
  color: #0f1720 !important;
}

/* Nav buttons — high contrast */
section[data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  background: #ffffff !important;
  color: #15202b !important;
  border: 1px solid #94a3b8 !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding: 0.6rem 0.9rem !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  border-color: #0f766e !important;
  color: #0f766e !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] {
  background: #0f766e !important;
  color: #ffffff !important;
  border-color: #0f766e !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"]:hover {
  color: #ffffff !important;
  background: #0d9488 !important;
}

.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  color: #15202b !important;
}
.stApp .stCaption, .stApp [data-testid="stCaptionContainer"] {
  color: #3d4f61 !important;
}

.hero-brand {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 2.2rem !important;
  font-weight: 600 !important;
  color: #0f766e !important;
  margin: 0 0 0.4rem 0 !important;
}
.hero-sub {
  color: #3d4f61 !important;
  font-size: 1.05rem !important;
  line-height: 1.5 !important;
  margin-bottom: 1.25rem !important;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0.75rem 0 1.25rem 0;
}
@media (min-width: 900px) {
  .metric-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
.metric-card {
  background: #ffffff;
  border: 1px solid #c5d0db;
  border-radius: 10px;
  padding: 1rem 1.1rem;
}
.metric-label {
  color: #3d4f61 !important;
  font-size: 0.75rem !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600 !important;
}
.metric-value {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 1.25rem !important;
  color: #0f766e !important;
  margin-top: 0.35rem !important;
  font-weight: 600 !important;
}
.chip-row { margin: 0.4rem 0 1rem 0; line-height: 2.1; }
.chip {
  display: inline-block;
  background: #ccfbf1;
  color: #115e59 !important;
  border: 1px solid #5eead4;
  border-radius: 6px;
  padding: 0.2rem 0.65rem;
  font-size: 0.85rem;
  margin: 0.15rem 0.3rem 0.15rem 0;
  font-family: 'IBM Plex Mono', monospace;
  font-weight: 600;
}
.trace-box {
  background: #ffffff;
  border: 1px solid #c5d0db;
  border-left: 4px solid #0f766e;
  padding: 0.85rem 1rem;
  margin: 0.5rem 0;
  border-radius: 0 8px 8px 0;
  color: #15202b !important;
}
div[data-testid="stMetricValue"] { color: #0f766e !important; }
div[data-testid="stMetricLabel"] { color: #3d4f61 !important; }

/* Primary CTA: always white text on teal (incl. hover) */
.stApp .stButton > button[kind="primary"],
.stApp .stButton > button[data-testid="baseButton-primary"],
.stApp button[data-testid="stBaseButton-primary"],
.stApp [data-testid="stButton"] button[kind="primary"] {
  background-color: #0f766e !important;
  background-image: none !important;
  color: #ffffff !important;
  border: 1px solid #0f766e !important;
  font-weight: 700 !important;
}
.stApp .stButton > button[kind="primary"] *,
.stApp .stButton > button[data-testid="baseButton-primary"] *,
.stApp button[data-testid="stBaseButton-primary"] *,
.stApp [data-testid="stButton"] button[kind="primary"] * {
  color: #ffffff !important;
}
.stApp .stButton > button[kind="primary"]:hover,
.stApp .stButton > button[data-testid="baseButton-primary"]:hover,
.stApp button[data-testid="stBaseButton-primary"]:hover,
.stApp [data-testid="stButton"] button[kind="primary"]:hover,
.stApp .stButton > button[kind="primary"]:focus,
.stApp .stButton > button[data-testid="baseButton-primary"]:focus,
.stApp button[data-testid="stBaseButton-primary"]:focus {
  background-color: #0d9488 !important;
  background-image: none !important;
  color: #ffffff !important;
  border-color: #0d9488 !important;
}
.stApp .stButton > button[kind="primary"]:hover *,
.stApp .stButton > button[data-testid="baseButton-primary"]:hover *,
.stApp button[data-testid="stBaseButton-primary"]:hover * {
  color: #ffffff !important;
}
</style>
""",
    unsafe_allow_html=True,
)


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


def page_overview():
    st.markdown('<p class="hero-brand">ICOT-RAG</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">Facet-aware Iterative Chain-of-Thought RAG for IoT cybersecurity — '
        "built for research (not a chatbot). Demo for project review.</p>",
        unsafe_allow_html=True,
    )

    metrics = [
        ("KB documents", "~1,820"),
        ("Sources", "MITRE · VARIoT · IoT-23"),
        ("Eval questions", "50"),
        ("Main claim", "Multi-facet retrieval ↑"),
    ]
    cards = "".join(
        f'<div class="metric-card"><div class="metric-label">{lab}</div>'
        f'<div class="metric-value">{val}</div></div>'
        for lab, val in metrics
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)

    st.markdown("### What we built")
    st.markdown(
        """
1. **Unified IoT security KB** — MITRE ATT&CK (techniques/mitigations), VARIoT (CVEs/exploits), IoT-23 (malware behaviour).  
2. **Facet-aware ICOT loop** — retrieve → reason (which evidence facets are missing?) → re-retrieve from the right source.  
3. **Answer-context filtering** — don’t dump 15–20 docs into the LLM; keep a tight facet-balanced set.  
4. **Baselines + evaluation** — vanilla RAG, Zeng-style prompt-only ICoT, facet ICOT; hard metrics + LLM-as-judge.  
5. **Explainable trace** — per-iteration thought, confidence, facets, next source, retrieved IDs.
"""
    )

    st.markdown("### Evidence facets")
    chips = " ".join(
        f'<span class="chip">{f}</span>'
        for f in ["behaviour", "technique", "vulnerability", "exploit", "mitigation"]
    )
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)

    st.markdown("### Positioning")
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
                    "Work": "ChatIoT",
                    "Retrieval": "Multi-retriever (single pass)",
                    "Iteration": "No",
                    "Facet routing": "Selector",
                },
                {
                    "Work": "This work (ICOT-RAG)",
                    "Retrieval": "Unified multi-source RAG",
                    "Iteration": "Yes",
                    "Facet routing": "Yes + filter + trace",
                },
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def page_demo():
    st.header("Live demo")
    st.caption(
        "Runs the real facet-ICOT pipeline (needs `.env` with `LLM_PROVIDER` + API key). "
        "First load downloads/loads the embedding model — wait once."
    )

    questions = load_eval_questions()
    categories = sorted({q.get("category", "general") for q in questions})
    cat_choice = st.selectbox(
        "Category filter",
        ["All"] + categories,
        help=f"{len(questions)} questions in the eval set",
    )
    samples = [
        q
        for q in questions
        if cat_choice == "All" or q.get("category") == cat_choice
    ]
    labels = {
        f"{q['id']} [{q.get('category', '?')}]: "
        f"{q['question'][:80]}{'…' if len(q['question']) > 80 else ''}": q
        for q in samples
    }

    choice = st.selectbox(
        f"Sample question ({len(samples)} shown)",
        ["(custom)"] + list(labels.keys()),
    )
    if choice == "(custom)":
        question = st.text_area(
            "Your question",
            value="What network behaviours does Mirai show in the IoT-23 Capture-7-1 scenario?",
            height=90,
        )
        required = None
    else:
        q = labels[choice]
        question = q["question"]
        required = q.get("required_facets")
        st.markdown(
            "Required facets: "
            + '<span class="chip-row">'
            + " ".join(f'<span class="chip">{f}</span>' for f in (required or []))
            + "</span>",
            unsafe_allow_html=True,
        )

    iters = st.slider("Max ICOT iterations", 1, 3, 3)
    filter_ctx = st.checkbox("Answer-context filtering", value=True)

    if st.button("Run facet ICOT", type="primary"):
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
            st.info("Check `.env` (`LLM_PROVIDER=groq`, `GROQ_API_KEY=…`) and that Chroma exists under `artifacts/chroma_db`.")
            return

    result = st.session_state.get("last_result")
    if not result:
        st.info("Pick a question and click **Run facet ICOT**.")
        return

    st.subheader("Answer")
    st.markdown(result.get("answer") or "_(empty)_")

    covered = result.get("covered_facets") or []
    st.markdown("**Covered facets**")
    if covered:
        st.markdown(
            '<div class="chip-row">'
            + " ".join(f'<span class="chip">{f}</span>' for f in covered)
            + "</div>",
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Retrieved docs (full)**")
        docs = result.get("documents") or []
        st.write(f"{len(docs)} documents")
        for d in docs[:8]:
            meta = d.get("metadata") or {}
            st.caption(
                f"`{d.get('id')}` · {meta.get('source')} · "
                f"{meta.get('document_type') or meta.get('cve') or meta.get('malware_family') or ''}"
            )
    with c2:
        st.markdown("**Answer docs (filtered)**")
        adocs = result.get("answer_documents") or docs
        st.write(f"{len(adocs)} documents used for generation")
        for d in adocs:
            meta = d.get("metadata") or {}
            st.caption(f"`{d.get('id')}` · {meta.get('source')}")

    st.subheader("Explainable trace")
    for step in result.get("trace") or []:
        with st.expander(
            f"Iteration {step.get('iteration')} — "
            f"confidence={step.get('confidence')} · enough={step.get('enough_information')}"
        ):
            st.markdown(
                f'<div class="trace-box"><b>Thought</b><br/>{step.get("thought")}</div>',
                unsafe_allow_html=True,
            )
            st.write("Reason:", step.get("reason"))
            st.write("Covered facets:", step.get("covered_facets"))
            st.write("Missing facets:", step.get("missing_facets"))
            st.write("Next source:", step.get("next_source"))
            st.write("Search query:", step.get("search_query"))
            st.write("Retrieved IDs:", step.get("retrieved_document_ids"))


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


def page_results():
    st.header("Evaluation results")
    st.caption("Frozen numbers from `artifacts/evaluation/` — same story as the paper Results draft.")

    three = load_json("multifacet_three_way.json")
    if three:
        st.subheader("Main result — multi-facet, 3-way (n=12)")
        df = _hard_table_from_three_way(three)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.bar_chart(df.set_index("Method")[["Facet recall", "Source hit", "Judge overall"]])
        st.success(
            "Takeaway: Facet ICOT leads retrieval coverage; prompt-only ICoT is weakest; "
            "vanilla often still wins answer-style judge scores."
        )
    else:
        st.warning("Missing `multifacet_three_way.json`")

    ab = load_json("llm_iter_ablation.json")
    if ab and ab.get("summary"):
        st.subheader("Ablation — iteration budget")
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

    filt = load_json("answer_context_filter_compare.json")
    if filt and filt.get("summary"):
        st.subheader("Ablation — answer-context filter")
        s = filt["summary"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Full-context judge", f"{s.get('avg_full_context', 0):.2f}")
        c2.metric("Filtered judge", f"{s.get('avg_filtered', 0):.2f}")
        c3.metric("Delta", f"{s.get('delta', 0):+.2f}")

    st.subheader("Per-question judge (3-way)")
    if three and three.get("rows"):
        detail = []
        for r in three["rows"]:
            j = r.get("judges") or {}
            detail.append(
                {
                    "ID": r["id"],
                    "Vanilla": round(j.get("vanilla", {}).get("overall", 0), 2),
                    "Prompt-only": round(
                        j.get("prompt_only_icot", {}).get("overall", 0), 2
                    ),
                    "Facet ICOT": round(j.get("facet_icot", {}).get("overall", 0), 2),
                }
            )
        st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True)


def page_howto():
    st.header("How the pipeline works")
    st.markdown(
        """
```text
Question
   │
   ▼
Initial retrieve (Chroma top-k)
   │
   ▼
┌─ ICOT iteration (max 3) ──────────────────┐
│  Reason: facets covered? confidence?       │
│  If enough → stop                          │
│  Else → re-retrieve by next_source / facet │
└────────────────────────────────────────────┘
   │
   ▼
Filter answer docs (≤6, facet-balanced)
   │
   ▼
Generate structured IoT security report
   │
   ▼
Return answer + docs + covered_facets + trace
```
"""
    )
    st.markdown("### Repo map")
    st.code(
        """rag_icot/          # core library
  pipeline/        # RAGICOTPipeline
  components/      # retriever, reasoner, filter, prompt-only ICoT
  evaluation/      # baselines, metrics, judge
artifacts/evaluation/  # frozen result JSONs
paper/             # results_draft.md, methods_draft.md
streamlit_app.py   # this demo
""",
        language="text",
    )
    st.markdown(
        "Paper drafts: `paper/results_draft.md`, `paper/methods_draft.md`. "
        "Claim to emphasize: **facet-aware iterative retrieval improves multi-source coverage**; "
        "prompt-only ICoT is not enough; answer filtering matters."
    )


def main():
    pages = ["Overview", "Live demo", "Results", "How it works"]
    if "page" not in st.session_state:
        st.session_state.page = "Overview"

    with st.sidebar:
        st.markdown("### ICOT-RAG")
        st.caption("IoT cybersecurity · research demo")
        for name in pages:
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
        st.caption("Package: rag_icot")
        st.caption("LLM via .env → Groq / Gemini")

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
