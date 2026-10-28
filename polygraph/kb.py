"""Knowledge Base for Polygraph claim generator."""
import csv
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Mention:
    date: str
    value: dict
    row_id: str
    text: str


@dataclass
class FactTimeline:
    subject: str
    attribute: str
    mentions: list  # list of Mention, sorted by date

    def current_value(self) -> dict:
        """Return the most recent value (latest date)."""
        if not self.mentions:
            return {}
        latest_date = max(m.date for m in self.mentions)
        latest = [m for m in self.mentions if m.date == latest_date]
        if len(latest) == 1:
            return latest[0].value
        # Multiple mentions on latest date: use most common value
        from collections import Counter
        counts = Counter(json.dumps(m.value, sort_keys=True) for m in latest)
        most_common_str = counts.most_common(1)[0][0]
        return json.loads(most_common_str)

    def earliest_value(self) -> dict:
        """Return the earliest value."""
        if not self.mentions:
            return {}
        earliest_date = min(m.date for m in self.mentions)
        earliest = [m for m in self.mentions if m.date == earliest_date]
        return earliest[0].value

    def had_change(self) -> bool:
        """Return True if the value changed over time."""
        if len(self.mentions) < 2:
            return False
        first = self.earliest_value()
        last = self.current_value()
        return json.dumps(first, sort_keys=True) != json.dumps(last, sort_keys=True)

    def distinct_values(self) -> list:
        """Return list of (date, value) for distinct value changes, sorted by date."""
        seen = {}
        # Group by date, take most common per date
        from collections import Counter
        by_date = defaultdict(list)
        for m in self.mentions:
            by_date[m.date].append(m.value)
        
        result = []
        last_val_str = None
        for date in sorted(by_date.keys()):
            vals = by_date[date]
            counts = Counter(json.dumps(v, sort_keys=True) for v in vals)
            val_str = counts.most_common(1)[0][0]
            if val_str != last_val_str:
                result.append((date, json.loads(val_str)))
                last_val_str = val_str
        return result


class KnowledgeBase:
    def __init__(self, practice_csv: str, lexicon_json: str):
        self.timelines: dict[tuple, FactTimeline] = {}  # (subject, attribute) -> FactTimeline
        self.subjects: dict[str, dict] = {}  # name -> {aliases, attributes}
        self.events: dict[str, str] = {}  # event name -> date
        self._existing_texts: set = set()  # normalized existing texts
        self._load(practice_csv, lexicon_json)

    def _normalize_text(self, text: str) -> str:
        import re
        return re.sub(r'\s+', ' ', text.strip().lower())

    def _load(self, practice_csv: str, lexicon_json: str):
        # Load lexicon
        with open(lexicon_json, encoding="utf-8") as f:
            lexicon = json.load(f)
        for subj in lexicon["subjects"]:
            self.subjects[subj["name"]] = subj
        self.events = {e: None for e in lexicon["events"]}

        # Load practice.csv - only true rows
        raw_mentions: dict[tuple, list] = defaultdict(list)
        with open(practice_csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["label"] != "true":
                    continue
                self._existing_texts.add(self._normalize_text(row["text"]))
                try:
                    forms = json.loads(row["form"])
                except json.JSONDecodeError:
                    continue
                for entry in forms:
                    subj = entry.get("subject", "")
                    attr = entry.get("attribute", "")
                    val = entry.get("value", {})
                    if not subj or not attr or not val:
                        continue
                    mention = Mention(
                        date=row["date"],
                        value=val,
                        row_id=row["id"],
                        text=row["text"],
                    )
                    raw_mentions[(subj, attr)].append(mention)

        # Build FactTimelines, sorted by date
        for (subj, attr), mentions in raw_mentions.items():
            sorted_mentions = sorted(mentions, key=lambda m: m.date)
            self.timelines[(subj, attr)] = FactTimeline(
                subject=subj,
                attribute=attr,
                mentions=sorted_mentions,
            )

        # Extract event dates from KB
        for event_name in list(self.events.keys()):
            tl = self.timelines.get((event_name, "date"))
            if tl:
                # Use most confident date: latest mention with most common value
                cv = tl.current_value()
                if cv.get("kind") == "date" and len(cv.get("value", "")) == 10:
                    self.events[event_name] = cv["value"]
                else:
                    # Try to find full date mentions
                    full_dates = [
                        m.value["value"] for m in tl.mentions
                        if len(m.value.get("value", "")) == 10
                    ]
                    if full_dates:
                        from collections import Counter
                        self.events[event_name] = Counter(full_dates).most_common(1)[0][0]

    def get_timeline(self, subject: str, attribute: str) -> "FactTimeline | None":
        return self.timelines.get((subject, attribute))

    def all_timelines(self) -> list:
        return list(self.timelines.values())

    def get_subject(self, name: str) -> "dict | None":
        return self.subjects.get(name)

    def is_existing_text(self, text: str) -> bool:
        return self._normalize_text(text) in self._existing_texts

    def get_mentions_on_date(self, date: str) -> list:
        """Return all (subject, attribute, value) tuples for mentions on a given date."""
        results = []
        for (subj, attr), tl in self.timelines.items():
            for m in tl.mentions:
                if m.date == date:
                    results.append((subj, attr, m.value))
                    break  # one per (subj, attr) per date
        return results

    def link_facts(self) -> list:
        """Return (subject, link_attr, target_name, target_subject) tuples
        where a subject's attribute value is a name of another subject."""
        results = []
        for (subj, attr), tl in self.timelines.items():
            cv = tl.current_value()
            if cv.get("kind") == "name":
                target_name = cv["value"]
                if target_name in self.subjects:
                    results.append((subj, attr, target_name, target_name))
        return results
