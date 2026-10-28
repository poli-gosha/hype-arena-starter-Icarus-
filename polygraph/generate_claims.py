"""Run this script directly to generate claims."""
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from polygraph.kb import KnowledgeBase
    from polygraph.forge import generate
    from polygraph.validate import validate_claim
    from collections import defaultdict
    import csv, json

    BASE = os.path.dirname(os.path.dirname(__file__))
    kb = KnowledgeBase(
        os.path.join(BASE, "data/practice.csv"),
        os.path.join(BASE, "data/lexicon.json")
    )

    print(f"KB loaded: {len(kb.timelines)} timelines, {len(kb.subjects)} subjects")
    print(f"Event dates: {kb.events}")

    claims = generate(kb)

    # Validate
    problems = []
    for c in claims:
        issues = validate_claim(c)
        if issues:
            problems.append((c['id'], issues))

    if problems:
        print(f"\nVALIDATION PROBLEMS ({len(problems)}):")
        for cid, issues in problems[:20]:
            print(f"  {cid}: {issues}")
    else:
        print("\nAll claims valid!")

    # Write output
    os.makedirs(os.path.join(BASE, "output"), exist_ok=True)
    out_path = os.path.join(BASE, "output/claims_output.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "type", "text", "form", "label", "confidence"])
        w.writeheader()
        for c in claims:
            w.writerow({
                "id": c["id"],
                "type": c["type"],
                "text": c["text"],
                "form": json.dumps(c["form"]) if isinstance(c["form"], dict) else c["form"],
                "label": c.get("label", "true"),
                "confidence": c.get("confidence", 0.8)
            })

    print(f"\nWritten {len(claims)} claims to {out_path}")

    # Print type breakdown
    from collections import Counter
    types = Counter(c['type'] for c in claims)
    print("Type breakdown:", dict(types))

    # Print 10 sample claims (2 of each type)
    print("\n=== SAMPLE CLAIMS (2 per type) ===")
    by_type = defaultdict(list)
    for c in claims:
        by_type[c['type']].append(c)

    for ctype in ["fact", "compare", "change", "at_event", "relation"]:
        samples = by_type.get(ctype, [])[:2]
        for s in samples:
            print(f"\n[{s['type']}] {s['text']}")
            print(f"  form: {json.dumps(s['form'])}")
            print(f"  confidence: {s['confidence']}")


