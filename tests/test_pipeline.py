"""The whole system end to end on the practice data, with every 5th label hidden."""
import re
from dataclasses import replace

from polygraph import pipeline
from polygraph.linker import Linker
from polygraph.render import render
from polygraph.validate import validate


def test_linker_longest_name(lexicon):
    found = [m.subject for m in Linker(lexicon).find("Hooly AI Pro costs more than hooly  workspace and Hooly.")]
    assert found == ["Hooly AI Pro", "Hooly Workspace", "Hooly"]


def test_render():
    assert render({"kind": "money", "value": 59, "currency": "EUR", "per": "month"}) == "€59 per month"
    assert render({"kind": "quantity", "value": 2048, "unit": "customer"}) == "2,048 customers"
    assert render({"kind": "quantity", "value": 12, "unit": "person"}) == "12 people"
    assert render({"kind": "date", "value": "2026-07-01"}) == "1 July 2026"
    assert render({"kind": "duration", "value": 1.5, "unit": "s"}) == "1.5 seconds"
    assert render({"kind": "quantity", "value": 1.125, "unit": "GB"}) is None  # 3 decimals read as nothing


def test_end_to_end(lexicon, bundle):
    rows = [replace(r, label="" if i % 5 == 0 else r.label) for i, r in enumerate(bundle.rows)]
    res = pipeline.run(rows, lexicon, bundle)
    hidden = {r.id for r in rows if not r.label}
    assert {v.id for v in res.verdicts} == hidden
    for v in res.verdicts:
        assert v.label in ("true", "false", "unsure")
        assert (v.confidence is None) == (v.label == "unsure")
        assert v.confidence is None or 0.5 <= v.confidence <= 1
    assert len(res.claims) == 1000
    assert len({c.id for c in res.claims}) == 1000
    for c in res.claims:
        assert re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", c.id)
        assert not validate(c, lexicon), (c.text, validate(c, lexicon))


def test_dates_in_other_forms(tmp_path):
    from polygraph.tables import iso_date, read_rows
    assert iso_date("2026-4-7") == "2026-04-07"
    assert iso_date("2026/04/14") == iso_date("14.04.2026") == iso_date("2026-04-14T09:30:00Z") == "2026-04-14"
    assert iso_date("April 2026") == "2026-04-01" and iso_date("nonsense") is None and iso_date("2026-02-30") is None
    f = tmp_path / "u.csv"
    f.write_text("id,text,date,label\na,x,14.04.2026,TRUE\nb,y,,\nc,z,2026-05-01, False \n", encoding="utf-8")
    rows = read_rows(f)
    assert [(r.date, r.label, r.page) for r in rows] == [("2026-04-14", "true", 0), ("2026-04-14", "", 0), ("2026-05-01", "false", 1)]


def test_practice_rows_found_under_other_ids(bundle):
    """The input may give the practice rows ids of its own: they are matched by text and date."""
    rows = [replace(r, id=f"u{i}") for i, r in enumerate(bundle.rows[:50])]
    rows[3] = replace(rows[3], label="")  # an unlabelled row is never matched
    b = bundle.aligned(rows)
    assert all(r.id in b.forms for r in rows if r.label)
    assert rows[3].id not in b.forms
    assert b.forms["u0"] == bundle.forms[bundle.rows[0].id]


def test_feature_names_match_the_judge(lexicon):
    """polygraph/explain.py names every feature judge.row_features builds, in order."""
    from polygraph import explain, judge, truth
    from polygraph.model import Row
    row = Row("x", "Hooly Jules works in 8 languages.", "2026-09-08", "", 0)
    t = truth.build(lexicon, [row], {})
    info = {"trust_loo": 0.8, "size": 1, "false_labels": 0, "true_labels": 0, "unsure_labels": 0}
    x, _, _ = judge.row_features(row, [], t, info)
    assert len(explain.FEATURES) == len(x) + 3  # + the 3 page features of the second pass
