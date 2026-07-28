import json
from pathlib import Path

j = json.loads(
    Path(r"E:\ICOT-RAG\artifacts\evaluation\llm_judge_smoke.json").read_text(
        encoding="utf-8"
    )
)
a = json.loads(
    Path(r"E:\ICOT-RAG\artifacts\evaluation\llm_iter_ablation.json").read_text(
        encoding="utf-8"
    )
)

print("=== JUDGE SUMMARY ===")
print(json.dumps(j["summary"], indent=2))

print("\n=== JUDGE PER QUESTION ===")
wins = {"vanilla": 0, "icot": 0, "tie": 0}
for r in j["rows"]:
    v, i = r["judges"]["vanilla"], r["judges"]["facet_icot"]
    d = v["overall"] - i["overall"]
    if abs(d) < 1e-9:
        wins["tie"] += 1
        tag = "TIE"
    elif d > 0:
        wins["vanilla"] += 1
        tag = "V"
    else:
        wins["icot"] += 1
        tag = "I"
    print(
        f"{r['id']:<5} {r['category']:<14} "
        f"V={v['overall']:.2f} I={i['overall']:.2f} "
        f"d={d:+.2f} winner={tag}"
    )
    print(
        f"  V dims r/rel/t/f="
        f"{v['reliability']:.0f}/{v['relevance']:.0f}/"
        f"{v['technicality']:.0f}/{v['friendliness']:.0f} "
        f"| I {i['reliability']:.0f}/{i['relevance']:.0f}/"
        f"{i['technicality']:.0f}/{i['friendliness']:.0f}"
    )
    print(f"  Vjust: {(v.get('justification') or '')[:160]}")
    print(f"  Ijust: {(i.get('justification') or '')[:160]}")

print("\nWin counts:", wins)

print("\n=== HARD METRICS (judge run) ===")
for r in j["rows"]:
    v, i = r["vanilla"], r["facet_icot"]
    print(
        f"{r['id']:<5} V fac/kw/src="
        f"{v['facet_recall']:.2f}/{v['keyword_hit_rate']:.2f}/{v['source_hit_rate']:.2f} "
        f"docs={v['doc_count']} | I "
        f"{i['facet_recall']:.2f}/{i['keyword_hit_rate']:.2f}/{i['source_hit_rate']:.2f} "
        f"docs={i['doc_count']} iter={i['iterations']}"
    )

print("\n=== ABLATION SUMMARY ===")
print(json.dumps(a["summary"], indent=2))

print("\n=== ABLATION PER QUESTION ===")
for r in a["rows"]:
    print(r["id"], r["category"], r["required_facets"])
    for aid, p in r["ablations"].items():
        jdg = p["judge"]
        print(
            f"  {aid:<16} fac={p['facet_recall']:.2f} "
            f"kw={p['keyword_hit_rate']:.2f} src={p['source_hit_rate']:.2f} "
            f"docs={p['doc_count']} iter={p['iterations']} "
            f"judge={jdg['overall']:.2f} "
            f"rel={jdg['reliability']:.0f}/{jdg['relevance']:.0f}/"
            f"{jdg['technicality']:.0f}/{jdg['friendliness']:.0f}"
        )
        print(f"    just: {(jdg.get('justification') or '')[:140]}")
        print(f"    ans: {(p.get('answer_preview') or '')[:120].replace(chr(10),' ')}")
