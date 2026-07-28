import json
from pathlib import Path

d = json.loads(
    Path(r"E:/ICOT-RAG/artifacts/evaluation/multifacet_vanilla_vs_icot.json").read_text(
        encoding="utf-8"
    )
)
print("n", len(d["rows"]), "errors", d.get("errors"))
print("HARD", json.dumps(d["hard_summary"], indent=2))
print("JUDGE", json.dumps(d["judge_summary"], indent=2))
print("WINS", d["judge_wins"])
print()
print(f"{'ID':<5} {'V_fac':>5} {'I_fac':>5} {'V_src':>5} {'I_src':>5} {'V_j':>5} {'I_j':>5} {'Δj':>6}")
for r in d["rows"]:
    v, i = r["vanilla"], r["facet_icot"]
    vj, ij = r["judges"]["vanilla"]["overall"], r["judges"]["facet_icot"]["overall"]
    print(
        f"{r['id']:<5} {v['facet_recall']:5.2f} {i['facet_recall']:5.2f} "
        f"{v['source_hit_rate']:5.2f} {i['source_hit_rate']:5.2f} "
        f"{vj:5.2f} {ij:5.2f} {ij-vj:+6.2f}"
    )
