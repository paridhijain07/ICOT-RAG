"""Evaluation utilities for ICOT-RAG experiments."""

from rag_icot.evaluation.dataset import (
    EvalQuestion,
    load_eval_dataset,
    summarize_dataset,
)
from rag_icot.evaluation.baselines import (
    run_vanilla_rag,
    run_single_pass_rag,
    run_chatiot_style,
    run_facet_icot,
    run_prompt_only_icot,
    run_prompt_only_icot_stub,
)
from rag_icot.evaluation.metrics import (
    compute_facet_coverage,
    source_diversity,
    keyword_hits,
    source_hits,
    summarize_run,
)
from rag_icot.evaluation.ablations import (
    RETRIEVAL_ABLATIONS,
    LLM_ABLATIONS,
    run_retrieval_ablation,
    run_llm_ablation,
    summarize_ablation_table,
)
from rag_icot.evaluation.judge import (
    AnswerJudge,
    JUDGE_DIMENSIONS,
    summarize_judge_rows,
)

__all__ = [
    "EvalQuestion",
    "load_eval_dataset",
    "summarize_dataset",
    "run_vanilla_rag",
    "run_single_pass_rag",
    "run_chatiot_style",
    "run_facet_icot",
    "run_prompt_only_icot",
    "run_prompt_only_icot_stub",
    "compute_facet_coverage",
    "source_diversity",
    "keyword_hits",
    "source_hits",
    "summarize_run",
    "RETRIEVAL_ABLATIONS",
    "LLM_ABLATIONS",
    "run_retrieval_ablation",
    "run_llm_ablation",
    "summarize_ablation_table",
    "AnswerJudge",
    "JUDGE_DIMENSIONS",
    "summarize_judge_rows",
]
