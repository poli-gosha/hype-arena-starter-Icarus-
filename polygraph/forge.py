"""Claim generator (forge) for Polygraph."""
import json
import random
import re
from collections import defaultdict

from polygraph.kb import KnowledgeBase, FactTimeline
from polygraph.render import render_value, render_money, render_quantity, render_date, attr_to_words

# Seed for reproducibility
random.seed(2026)

# Number patterns to catch in compare texts
_DIGIT_RE = re.compile(r'\d')
_MONTH_RE = re.compile(
    r'\b(january|february|march|april|may|june|july|august|'
    r'september|october|november|december)\b', re.IGNORECASE
)
_TIME_RE = re.compile(
    r'\b(ago|yesterday|before|after|since|recently|previously|formerly|'
    r'used to|once|later|earlier|last|next|current|now|today|then|when)\b',
    re.IGNORECASE
)
_WORD_NUM_RE = re.compile(
    r'\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
    r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
    r'thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|'
    r'billion|a dozen|dozen|a few|a couple|several|many|numerous)\b',
    re.IGNORECASE
)


def _no_compare_violations(text: str) -> bool:
    """Return True if text has no digits, word numbers, months, or time words."""
    if _DIGIT_RE.search(text):
        return False
    if _WORD_NUM_RE.search(text):
        return False
    if _MONTH_RE.search(text):
        return False
    if _TIME_RE.search(text):
        return False
    return True


def _bool_attr_phrase(attribute: str) -> str:
    """Convert boolean attribute to readable phrase."""
    words = attr_to_words(attribute)
    return words


def _make_fact_text(subject: str, attribute: str, value: dict) -> str:
    """Generate fact claim text."""
    rendered = render_value(value)
    kind = value.get("kind")

    if kind == "boolean":
        phrase = _bool_attr_phrase(attribute)
        if value.get("value"):
            templates = [
                f"{subject} is {phrase}.",
                f"{subject} is {phrase} compliant.",
                f"{subject} supports {phrase}.",
                f"{subject} has {phrase} enabled.",
                f"{subject} offers {phrase}.",
            ]
            # Pick sensible template based on phrase
            if "certified" in phrase or "compliant" in phrase:
                return f"{subject} is {phrase}."
            elif phrase in ("open source", "self-hosted", "multi-region"):
                return f"{subject} is {phrase}."
            else:
                return f"{subject} has {phrase}."
        else:
            phrase = _bool_attr_phrase(attribute)
            return f"{subject} does not have {phrase}."

    if kind == "money":
        per = value.get("per")
        if per:
            templates = [
                f"{subject} costs {rendered}.",
                f"{subject} is priced at {rendered}.",
                f"{subject} is available for {rendered}.",
                f"The price of {subject} is {rendered}.",
                f"{subject} has a {rendered} price.",
            ]
        else:
            templates = [
                f"{subject} costs {rendered}.",
                f"The price of {subject} is {rendered}.",
                f"{subject} is priced at {rendered}.",
            ]
        return random.choice(templates)

    if kind == "quantity":
        unit = value.get("unit", "")
        templates = [
            f"{subject} has {rendered}.",
            f"{subject} supports {rendered}.",
            f"{subject} reached {rendered}.",
            f"{subject} counts {rendered}.",
            f"{rendered} are available in {subject}.",
        ]
        # Pick by unit type
        if "customer" in unit or "user" in unit:
            return f"{subject} has {rendered}."
        elif "language" in unit:
            opts = [
                f"{subject} supports {rendered}.",
                f"{subject} is available in {rendered}.",
            ]
            return random.choice(opts)
        elif "engineer" in unit or "employee" in unit or "person" in unit or "staff" in unit:
            return f"{subject} employs {rendered}."
        elif "talk" in unit or "session" in unit or "sponsor" in unit or "attendee" in unit:
            return f"{subject} has {rendered}."
        elif "seat" in unit or "ticket" in unit:
            return f"{subject} has capacity for {rendered}."
        elif "integration" in unit or "partner" in unit:
            return f"{subject} has {rendered}."
        elif "country" in unit or "region" in unit or "city" in unit:
            return f"{subject} is available in {rendered}."
        else:
            return f"{subject} has {rendered}."

    if kind == "date":
        templates = [
            f"{subject} launched on {rendered}.",
            f"{subject} was founded on {rendered}.",
            f"{subject} started on {rendered}.",
            f"{subject} began on {rendered}.",
            f"{subject} was established in {rendered}.",
        ]
        attr_low = attribute.lower()
        if "launch" in attr_low or "release" in attr_low:
            return f"{subject} launched on {rendered}."
        elif "found" in attr_low:
            return f"{subject} was founded on {rendered}."
        elif "join" in attr_low or "start" in attr_low:
            return f"{subject} joined on {rendered}."
        elif "date" == attr_low:
            return f"{subject} took place on {rendered}."
        else:
            return f"{subject} was established on {rendered}."

    if kind == "duration":
        attr_low = attribute.lower()
        templates = [
            f"{subject} has a {rendered} {attr_to_words(attribute)}.",
            f"The {attr_to_words(attribute)} of {subject} is {rendered}.",
            f"{subject} offers a {rendered} {attr_to_words(attribute)}.",
        ]
        if "trial" in attr_low:
            return f"{subject} offers a {rendered} free trial."
        elif "retention" in attr_low:
            return f"{subject} retains data for {rendered}."
        elif "uptime" in attr_low or "sla" in attr_low:
            return f"{subject} guarantees {rendered} uptime."
        elif "support" in attr_low or "response" in attr_low:
            return f"{subject} has a {rendered} support response time."
        elif "duration" in attr_low or "length" in attr_low:
            return f"{subject} lasts {rendered}."
        else:
            return f"{subject} has a {rendered} {attr_to_words(attribute)}."

    if kind == "percent":
        attr_low = attribute.lower()
        if "uptime" in attr_low or "sla" in attr_low or "availability" in attr_low:
            return f"{subject} guarantees {rendered} uptime."
        elif "discount" in attr_low:
            return f"{subject} offers a {rendered} discount."
        elif "growth" in attr_low:
            return f"{subject} achieved {rendered} growth."
        elif "open" in attr_low:
            return f"{subject} has an open rate of {rendered}."
        elif "accuracy" in attr_low or "precision" in attr_low:
            return f"{subject} achieves {rendered} accuracy."
        else:
            return f"{subject} has a {rendered} {attr_to_words(attribute)}."

    if kind == "version":
        attr_low = attribute.lower()
        if "version" in attr_low or "release" in attr_low:
            return f"{subject} is on version {rendered}."
        else:
            return f"The current version of {subject} is {rendered}."

    if kind == "name":
        attr_low = attribute.lower()
        words = attr_to_words(attribute)
        if "lead" in attr_low or "head" in attr_low or "director" in attr_low:
            return f"The {words} of {subject} is {rendered}."
        elif "partner" in attr_low or "integration" in attr_low:
            return f"{subject} partners with {rendered}."
        elif "employer" in attr_low or "company" in attr_low:
            return f"{subject} previously worked at {rendered}."
        elif "city" in attr_low or "location" in attr_low or "venue" in attr_low:
            return f"{subject} is located in {rendered}."
        elif "provider" in attr_low or "platform" in attr_low or "host" in attr_low:
            return f"{subject} runs on {rendered}."
        else:
            return f"The {words} of {subject} is {rendered}."

    return f"{subject} has {attribute} of {rendered}."


def _make_compare_text(left_subj: str, right_subj: str, attribute: str, op: str, value_kind: str) -> str:
    """Generate compare claim text with NO numbers, NO months, NO time words."""
    attr_low = attribute.lower()

    if value_kind == "date":
        if op == "gt":
            # "after" and "later than" are valid date compare phrases per spec
            # but our validator also bans time words - use safe phrasing
            return f"{left_subj} is newer than {right_subj}."
        elif op == "lt":
            return f"{left_subj} is older than {right_subj}."
        else:
            return f"{left_subj} launched at the same time as {right_subj}."

    # amount-based comparisons
    if op == "gt":
        if "price" in attr_low or "cost" in attr_low or "fee" in attr_low or value_kind == "money":
            opts = [
                f"{left_subj} costs more than {right_subj}.",
                f"{left_subj} has a higher price than {right_subj}.",
                f"{left_subj} is more expensive than {right_subj}.",
            ]
        elif "user" in attr_low or "customer" in attr_low or "active" in attr_low:
            opts = [
                f"{left_subj} has more active users than {right_subj}.",
                f"{left_subj} serves more customers than {right_subj}.",
            ]
        elif "language" in attr_low:
            opts = [
                f"{left_subj} supports more languages than {right_subj}.",
            ]
        elif "employee" in attr_low or "engineer" in attr_low or "team" in attr_low or "staff" in attr_low or "headcount" in attr_low:
            opts = [
                f"{left_subj} has a larger team than {right_subj}.",
                f"{left_subj} employs more staff than {right_subj}.",
            ]
        elif "attendee" in attr_low or "seat" in attr_low or "capacity" in attr_low:
            opts = [
                f"{left_subj} has more attendees than {right_subj}.",
                f"{left_subj} has greater capacity than {right_subj}.",
            ]
        elif "uptime" in attr_low or "availability" in attr_low or "sla" in attr_low or value_kind == "percent":
            opts = [
                f"{left_subj} has higher uptime than {right_subj}.",
                f"{left_subj} offers a higher SLA than {right_subj}.",
            ]
        elif value_kind == "duration":
            opts = [
                f"{left_subj} has a longer {attr_to_words(attribute)} than {right_subj}.",
                f"{left_subj} offers a longer {attr_to_words(attribute)} than {right_subj}.",
            ]
        else:
            opts = [
                f"{left_subj} has more {attr_to_words(attribute)} than {right_subj}.",
                f"{left_subj} has a higher {attr_to_words(attribute)} than {right_subj}.",
            ]
        return random.choice(opts)

    elif op == "lt":
        if "price" in attr_low or "cost" in attr_low or "fee" in attr_low or value_kind == "money":
            opts = [
                f"{left_subj} costs less than {right_subj}.",
                f"{left_subj} has a lower price than {right_subj}.",
                f"{left_subj} is cheaper than {right_subj}.",
            ]
        elif "user" in attr_low or "customer" in attr_low:
            opts = [
                f"{left_subj} has fewer customers than {right_subj}.",
                f"{left_subj} serves fewer users than {right_subj}.",
            ]
        elif "language" in attr_low:
            opts = [
                f"{left_subj} supports fewer languages than {right_subj}.",
            ]
        elif "employee" in attr_low or "engineer" in attr_low or "team" in attr_low or "staff" in attr_low or "headcount" in attr_low:
            opts = [
                f"{left_subj} has a smaller team than {right_subj}.",
                f"{left_subj} employs fewer staff than {right_subj}.",
            ]
        elif "uptime" in attr_low or "availability" in attr_low or "sla" in attr_low or value_kind == "percent":
            opts = [
                f"{left_subj} has lower uptime than {right_subj}.",
            ]
        elif value_kind == "duration":
            opts = [
                f"{left_subj} has a shorter {attr_to_words(attribute)} than {right_subj}.",
            ]
        else:
            opts = [
                f"{left_subj} has fewer {attr_to_words(attribute)} than {right_subj}.",
                f"{left_subj} has a lower {attr_to_words(attribute)} than {right_subj}.",
            ]
        return random.choice(opts)

    else:  # eq
        if "price" in attr_low or "cost" in attr_low or value_kind == "money":
            return f"{left_subj} costs the same as {right_subj}."
        else:
            return f"{left_subj} has the same {attr_to_words(attribute)} as {right_subj}."


def _compare_values(v1: dict, v2: dict):
    """
    Compare two values of the same kind.
    Return 'gt' if v1 > v2, 'lt' if v1 < v2, 'eq' if equal, None if incomparable.
    """
    kind = v1.get("kind")
    if kind != v2.get("kind"):
        return None
    if kind in ("money", "quantity", "percent", "duration"):
        a = v1.get("value", 0)
        b = v2.get("value", 0)
        # For money/duration check same unit
        if kind == "money" and v1.get("currency") != v2.get("currency"):
            return None
        if kind in ("quantity", "duration") and v1.get("unit") != v2.get("unit"):
            return None
        if a > b:
            return "gt"
        elif a < b:
            return "lt"
        else:
            return "eq"
    elif kind == "date":
        a = v1.get("value", "")
        b = v2.get("value", "")
        # Only compare full dates (YYYY-MM-DD) or years
        if len(a) != len(b):
            return None
        if a > b:
            return "gt"
        elif a < b:
            return "lt"
        else:
            return "eq"
    return None


def _render_change_text(subject: str, attribute: str, from_val: dict, to_val: dict) -> str:
    """Generate change claim text."""
    from_str = render_value(from_val)
    to_str = render_value(to_val)
    kind = from_val.get("kind")

    if kind == "money":
        a = from_val.get("value", 0)
        b = to_val.get("value", 0)
        if a < b:
            opts = [
                f"{subject} went from {from_str} to {to_str}.",
                f"{subject} costs {to_str}, up from {from_str}.",
                f"The price of {subject} rose from {from_str} to {to_str}.",
            ]
        elif a > b:
            opts = [
                f"{subject} went from {from_str} to {to_str}.",
                f"{subject} costs {to_str}, down from {from_str}.",
                f"The price of {subject} fell from {from_str} to {to_str}.",
            ]
        else:
            return f"{subject} maintained its price at {to_str}."
        return random.choice(opts)

    if kind == "quantity":
        a = from_val.get("value", 0)
        b = to_val.get("value", 0)
        if a < b:
            opts = [
                f"{subject} grew from {from_str} to {to_str}.",
                f"{subject} increased from {from_str} to {to_str}.",
                f"{subject} now has {to_str}, up from {from_str}.",
            ]
        elif a > b:
            opts = [
                f"{subject} decreased from {from_str} to {to_str}.",
                f"{subject} went from {from_str} to {to_str}.",
                f"{subject} now has {to_str}, down from {from_str}.",
            ]
        else:
            opts = [f"{subject} went from {from_str} to {to_str}."]
        return random.choice(opts)

    if kind == "date":
        return f"The date of {subject} moved from {from_str} to {to_str}."

    if kind == "percent":
        a = from_val.get("value", 0)
        b = to_val.get("value", 0)
        if a < b:
            return f"{subject} rose from {from_str} to {to_str}."
        elif a > b:
            return f"{subject} fell from {from_str} to {to_str}."
        else:
            return f"{subject} stayed at {to_str}."

    if kind == "version":
        return f"{subject} was updated from version {from_str} to {to_str}."

    if kind == "duration":
        a = from_val.get("value", 0)
        b = to_val.get("value", 0)
        if a < b:
            return f"The {attr_to_words(attribute)} of {subject} extended from {from_str} to {to_str}."
        else:
            return f"The {attr_to_words(attribute)} of {subject} shortened from {from_str} to {to_str}."

    # Fallback
    return f"{subject} changed {attr_to_words(attribute)} from {from_str} to {to_str}."


def _make_relation_text(parent_subj: str, link_attr: str, target_name: str, rel_attribute: str, rel_value: dict) -> str:
    """Generate relation claim text."""
    link_words = attr_to_words(link_attr)
    rendered = render_value(rel_value)
    kind = rel_value.get("kind")
    attr_words = attr_to_words(rel_attribute)

    if kind == "date":
        attr_low = rel_attribute.lower()
        if "join" in attr_low or "start" in attr_low:
            opts = [
                f"The {link_words} of {parent_subj} joined on {rendered}.",
                f"{parent_subj}'s {link_words} started on {rendered}.",
            ]
        elif "previous_employer" in attr_low or "employer" in attr_low:
            opts = [
                f"The {link_words} of {parent_subj} previously worked at {rendered}.",
            ]
        else:
            opts = [
                f"The {link_words} of {parent_subj} has a {attr_words} of {rendered}.",
            ]
        return random.choice(opts)

    if kind == "name":
        return f"The {link_words} of {parent_subj} previously worked at {rendered}."

    if kind == "quantity":
        return f"The {link_words} of {parent_subj} manages {rendered}."

    if kind == "percent":
        return f"The {link_words} of {parent_subj} has a {attr_words} of {rendered}."

    if kind == "version":
        return f"The {link_words} of {parent_subj} works on version {rendered}."

    if kind == "duration":
        return f"The {link_words} of {parent_subj} has a {attr_words} of {rendered}."

    return f"The {link_words} of {parent_subj} has {attr_words} of {rendered}."


def _make_at_event_text(subject: str, attribute: str, event: str, value: dict) -> str:
    """Generate at_event claim text."""
    rendered = render_value(value)
    kind = value.get("kind")

    event_phrases = ["at", "during", "at the time of", "on the day of"]
    ep = random.choice(event_phrases)

    attr_low = attribute.lower()

    if kind == "date":
        if any(w in attr_low for w in ("launch", "release", "released", "launched")):
            return f"{subject} was launched {ep} {event}."
        elif attr_low == "date":
            return f"{subject} was held {ep} {event}."
        else:
            return f"{subject} recorded its {attr_to_words(attribute)} {ep} {event}."

    if kind == "quantity":
        unit = value.get("unit", "")
        if "language" in unit:
            opts = [
                f"{subject} supported {rendered} {ep} {event}.",
                f"{subject} was available in {rendered} {ep} {event}.",
            ]
        elif "customer" in unit or "user" in unit:
            opts = [
                f"{subject} had {rendered} {ep} {event}.",
            ]
        elif "attendee" in unit or "seat" in unit:
            opts = [
                f"{subject} drew {rendered} {ep} {event}.",
                f"{subject} had {rendered} {ep} {event}.",
            ]
        else:
            opts = [
                f"{subject} had {rendered} {ep} {event}.",
            ]
        return random.choice(opts)

    if kind == "money":
        return f"{subject} was priced at {rendered} {ep} {event}."

    if kind == "percent":
        return f"{subject} had {rendered} {ep} {event}."

    if kind == "version":
        return f"{subject} was at version {rendered} {ep} {event}."

    if kind == "boolean":
        phrase = _bool_attr_phrase(attribute)
        if value.get("value"):
            return f"{subject} had {phrase} {ep} {event}."
        else:
            return f"{subject} did not have {phrase} {ep} {event}."

    if kind == "duration":
        return f"{subject} had a {rendered} {attr_to_words(attribute)} {ep} {event}."

    return f"{subject} had {rendered} {ep} {event}."


def generate(kb: KnowledgeBase) -> list:
    """Generate exactly 1000 claim dicts."""
    claims = []
    existing_texts = set()  # normalized texts already generated
    counters = {"fact": 0, "compare": 0, "change": 0, "at_event": 0, "relation": 0}
    targets = {"fact": 500, "compare": 250, "change": 150, "at_event": 80, "relation": 20}
    claim_id_counter = [1]

    def norm(text):
        import re
        return re.sub(r'\s+', ' ', text.strip().lower())

    def is_dup(text):
        n = norm(text)
        if n in existing_texts:
            return True
        if kb.is_existing_text(text):
            return True
        return False

    def add_claim(ctype, text, form, confidence=0.8):
        if is_dup(text):
            return False
        if len(text) > 300:
            return False
        cid = f"claim-{claim_id_counter[0]:04d}"
        claim_id_counter[0] += 1
        claims.append({
            "id": cid,
            "type": ctype,
            "text": text,
            "form": form,
            "label": "true",
            "confidence": round(confidence, 4),
        })
        existing_texts.add(norm(text))
        counters[ctype] += 1
        return True

    all_tls = kb.all_timelines()
    max_mentions = max((len(tl.mentions) for tl in all_tls), default=1)

    def confidence_for(tl):
        return min(1.0, 0.7 + 0.3 * len(tl.mentions) / max_mentions)

    # ---- RELATION claims (20 target) ----
    link_facts = kb.link_facts()
    random.shuffle(link_facts)
    relation_templates_used = set()

    for (parent_subj, link_attr, target_name, _) in link_facts:
        if counters["relation"] >= targets["relation"]:
            break
        # Find attributes of the target subject
        target_tls = [
            tl for tl in all_tls
            if tl.subject == target_name
            and tl.current_value().get("kind") in ("date", "name", "quantity", "percent")
        ]
        random.shuffle(target_tls)
        for target_tl in target_tls:
            rel_val = target_tl.current_value()
            if not rel_val:
                continue
            text = _make_relation_text(parent_subj, link_attr, target_name, target_tl.attribute, rel_val)
            form = {
                "subject": parent_subj,
                "link": link_attr,
                "target": target_name,
                "attribute": target_tl.attribute,
                "value": rel_val,
            }
            conf = confidence_for(target_tl)
            if add_claim("relation", text, form, conf):
                break

    # ---- AT_EVENT claims (80 target) ----
    event_dates = {k: v for k, v in kb.events.items() if v}
    at_event_added = set()

    for event_name, event_date in event_dates.items():
        if counters["at_event"] >= targets["at_event"]:
            break
        # Find fact mentions on this date that are not the event itself
        event_mentions = []
        for (subj, attr), tl in kb.timelines.items():
            if subj == event_name:
                continue
            for m in tl.mentions:
                if m.date == event_date:
                    event_mentions.append((subj, attr, m.value, tl))
                    break
        random.shuffle(event_mentions)
        for (subj, attr, val, tl) in event_mentions:
            if counters["at_event"] >= targets["at_event"]:
                break
            key = (subj, attr, event_name)
            if key in at_event_added:
                continue
            text = _make_at_event_text(subj, attr, event_name, val)
            form = {
                "subject": subj,
                "attribute": attr,
                "event": event_name,
                "value": val,
            }
            conf = confidence_for(tl)
            if add_claim("at_event", text, form, conf):
                at_event_added.add(key)

    # If still need more at_event, try with alternate event phrases
    if counters["at_event"] < targets["at_event"]:
        for event_name, event_date in event_dates.items():
            if counters["at_event"] >= targets["at_event"]:
                break
            event_mentions = []
            for (subj, attr), tl in kb.timelines.items():
                if subj == event_name:
                    continue
                for m in tl.mentions:
                    if m.date == event_date:
                        event_mentions.append((subj, attr, m.value, tl))
            for (subj, attr, val, tl) in event_mentions:
                if counters["at_event"] >= targets["at_event"]:
                    break
                # Try different text templates
                rendered = render_value(val)
                alt_texts = [
                    f"At {event_name}, {subj} had {rendered}.",
                    f"During {event_name}, {subj} had {rendered}.",
                    f"{subj} reported {rendered} at {event_name}.",
                    f"{subj} showed {rendered} during {event_name}.",
                ]
                for text in alt_texts:
                    form = {
                        "subject": subj,
                        "attribute": attr,
                        "event": event_name,
                        "value": val,
                    }
                    if add_claim("at_event", text, form, confidence_for(tl)):
                        break

    # ---- CHANGE claims (150 target) ----
    change_tls = [tl for tl in all_tls if tl.had_change()]
    random.shuffle(change_tls)

    for tl in change_tls:
        if counters["change"] >= targets["change"]:
            break
        distinct = tl.distinct_values()
        if len(distinct) < 2:
            continue
        # Use first and last distinct values
        from_date, from_val = distinct[0]
        to_date, to_val = distinct[-1]

        # Skip if same rendered value
        if render_value(from_val) == render_value(to_val):
            continue

        # Skip if values can't be coherently changed (name->name ok, money->money ok, etc.)
        if from_val.get("kind") != to_val.get("kind"):
            continue

        kind = from_val.get("kind")
        # Skip booleans (hard to express "changed from true to false" cleanly)
        if kind == "boolean":
            continue

        text = _render_change_text(tl.subject, tl.attribute, from_val, to_val)
        form = {
            "subject": tl.subject,
            "attribute": tl.attribute,
            "from": from_val,
            "to": to_val,
        }
        conf = confidence_for(tl)
        if add_claim("change", text, form, conf):
            pass

    # If need more change claims, try with middle values too
    if counters["change"] < targets["change"]:
        for tl in change_tls:
            if counters["change"] >= targets["change"]:
                break
            distinct = tl.distinct_values()
            if len(distinct) < 3:
                continue
            # Try adjacent pairs
            for i in range(len(distinct) - 1):
                if counters["change"] >= targets["change"]:
                    break
                from_date, from_val = distinct[i]
                to_date, to_val = distinct[i + 1]
                if from_val.get("kind") != to_val.get("kind"):
                    continue
                if from_val.get("kind") == "boolean":
                    continue
                if render_value(from_val) == render_value(to_val):
                    continue
                text = _render_change_text(tl.subject, tl.attribute, from_val, to_val)
                form = {
                    "subject": tl.subject,
                    "attribute": tl.attribute,
                    "from": from_val,
                    "to": to_val,
                }
                add_claim("change", text, form, confidence_for(tl))

    # ---- COMPARE claims (250 target) ----
    # Group timelines by attribute + value kind
    attr_groups = defaultdict(list)
    for tl in all_tls:
        cv = tl.current_value()
        if not cv:
            continue
        kind = cv.get("kind")
        if kind not in ("money", "quantity", "percent", "duration", "date"):
            continue
        # For money: group by attribute + currency + per
        if kind == "money":
            key = (tl.attribute, "money", cv.get("currency"), cv.get("per"))
        elif kind == "quantity":
            key = (tl.attribute, "quantity", cv.get("unit"))
        elif kind == "duration":
            key = (tl.attribute, "duration", cv.get("unit"))
        else:
            key = (tl.attribute, kind, None)
        attr_groups[key].append(tl)

    compare_pairs = []
    for key, group in attr_groups.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                tl1, tl2 = group[i], group[j]
                if tl1.subject == tl2.subject:
                    continue
                v1 = tl1.current_value()
                v2 = tl2.current_value()
                op = _compare_values(v1, v2)
                if op is None:
                    continue
                compare_pairs.append((tl1, tl2, key[1], op, key))

    random.shuffle(compare_pairs)

    def _all_compare_texts(ls, rs, attribute, op, value_kind):
        """Return all valid phrasings for a compare pair."""
        attr_low = attribute.lower()
        candidates = []
        if value_kind == "date":
            if op == "gt":
                candidates = [
                    f"{ls} is newer than {rs}.",
                    f"{rs} is older than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} is older than {rs}.",
                    f"{rs} is newer than {ls}.",
                ]
            else:
                candidates = [f"{ls} is as old as {rs}."]
        elif value_kind == "money" or "price" in attr_low or "cost" in attr_low or "fee" in attr_low:
            if op == "gt":
                candidates = [
                    f"{ls} costs more than {rs}.",
                    f"{ls} has a higher price than {rs}.",
                    f"{ls} is more expensive than {rs}.",
                    f"{rs} costs less than {ls}.",
                    f"{rs} is cheaper than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} costs less than {rs}.",
                    f"{ls} has a lower price than {rs}.",
                    f"{ls} is cheaper than {rs}.",
                    f"{rs} costs more than {ls}.",
                    f"{rs} is more expensive than {ls}.",
                ]
            else:
                candidates = [
                    f"{ls} costs the same as {rs}.",
                    f"{ls} has the same price as {rs}.",
                    f"{rs} costs the same as {ls}.",
                ]
        elif "language" in attr_low:
            if op == "gt":
                candidates = [
                    f"{ls} supports more languages than {rs}.",
                    f"{ls} has more language support than {rs}.",
                    f"{rs} supports fewer languages than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} supports fewer languages than {rs}.",
                    f"{rs} supports more languages than {ls}.",
                ]
            else:
                candidates = [
                    f"{ls} supports as many languages as {rs}.",
                    f"{ls} has the same language support as {rs}.",
                ]
        elif "user" in attr_low or "customer" in attr_low:
            if op == "gt":
                candidates = [
                    f"{ls} has more active users than {rs}.",
                    f"{ls} serves more customers than {rs}.",
                    f"{rs} has fewer customers than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} has fewer active users than {rs}.",
                    f"{ls} serves fewer customers than {rs}.",
                    f"{rs} has more customers than {ls}.",
                ]
            else:
                candidates = [f"{ls} has as many users as {rs}."]
        elif "employee" in attr_low or "engineer" in attr_low or "team" in attr_low or "staff" in attr_low or "headcount" in attr_low or "crew" in attr_low:
            if op == "gt":
                candidates = [
                    f"{ls} has a larger team than {rs}.",
                    f"{ls} employs more staff than {rs}.",
                    f"{rs} has a smaller team than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} has a smaller team than {rs}.",
                    f"{ls} employs fewer staff than {rs}.",
                    f"{rs} has a larger team than {ls}.",
                ]
            else:
                candidates = [f"{ls} has the same team size as {rs}."]
        elif "attendee" in attr_low or "seat" in attr_low or "capacity" in attr_low:
            if op == "gt":
                candidates = [
                    f"{ls} has more attendees than {rs}.",
                    f"{ls} has greater capacity than {rs}.",
                    f"{rs} has fewer attendees than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} has fewer attendees than {rs}.",
                    f"{rs} has more attendees than {ls}.",
                ]
            else:
                candidates = [f"{ls} has the same capacity as {rs}."]
        elif "talk" in attr_low or "session" in attr_low or "sponsor" in attr_low:
            if op == "gt":
                candidates = [
                    f"{ls} has more {attr_to_words(attribute)} than {rs}.",
                    f"{rs} has fewer {attr_to_words(attribute)} than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} has fewer {attr_to_words(attribute)} than {rs}.",
                    f"{rs} has more {attr_to_words(attribute)} than {ls}.",
                ]
            else:
                candidates = [f"{ls} has the same {attr_to_words(attribute)} as {rs}."]
        elif value_kind == "percent":
            awords = attr_to_words(attribute)
            if op == "gt":
                candidates = [
                    f"{ls} has a higher {awords} than {rs}.",
                    f"{rs} has a lower {awords} than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} has a lower {awords} than {rs}.",
                    f"{rs} has a higher {awords} than {ls}.",
                ]
            else:
                candidates = [f"{ls} has the same {awords} as {rs}."]
        elif value_kind == "duration":
            awords = attr_to_words(attribute)
            if op == "gt":
                candidates = [
                    f"{ls} has a longer {awords} than {rs}.",
                    f"{ls} offers a longer {awords} than {rs}.",
                    f"{rs} has a shorter {awords} than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} has a shorter {awords} than {rs}.",
                    f"{rs} has a longer {awords} than {ls}.",
                ]
            else:
                candidates = [f"{ls} has the same {awords} as {rs}."]
        else:
            awords = attr_to_words(attribute)
            if op == "gt":
                candidates = [
                    f"{ls} has more {awords} than {rs}.",
                    f"{ls} has a higher {awords} than {rs}.",
                    f"{rs} has fewer {awords} than {ls}.",
                ]
            elif op == "lt":
                candidates = [
                    f"{ls} has fewer {awords} than {rs}.",
                    f"{ls} has a lower {awords} than {rs}.",
                    f"{rs} has more {awords} than {ls}.",
                ]
            else:
                candidates = [f"{ls} has the same {awords} as {rs}."]
        return [t for t in candidates if _no_compare_violations(t) and len(t) <= 300]

    # Collect all candidate compare claims
    _compare_candidates = []
    _seen_compare_texts = set()
    for (tl1, tl2, value_kind, op, key) in compare_pairs:
        attribute = tl1.attribute
        conf = min(confidence_for(tl1), confidence_for(tl2))
        # Forward
        for text in _all_compare_texts(tl1.subject, tl2.subject, attribute, op, value_kind):
            if text not in _seen_compare_texts:
                _seen_compare_texts.add(text)
                form = {"left": {"subject": tl1.subject, "attribute": attribute},
                        "right": {"subject": tl2.subject, "attribute": attribute}, "op": op}
                _compare_candidates.append((text, form, conf))
        # Reversed
        rev_op = {"gt": "lt", "lt": "gt", "eq": "eq"}[op]
        for text in _all_compare_texts(tl2.subject, tl1.subject, attribute, rev_op, value_kind):
            if text not in _seen_compare_texts:
                _seen_compare_texts.add(text)
                form = {"left": {"subject": tl2.subject, "attribute": attribute},
                        "right": {"subject": tl1.subject, "attribute": attribute}, "op": rev_op}
                _compare_candidates.append((text, form, conf))

    random.shuffle(_compare_candidates)
    for text, form, conf in _compare_candidates:
        if counters["compare"] >= targets["compare"]:
            break
        add_claim("compare", text, form, conf)

    # ---- FACT claims (500 target) ----
    # Sort by mention count (most supported first)
    sorted_tls = sorted(all_tls, key=lambda tl: len(tl.mentions), reverse=True)
    fact_templates_cycle = {}

    # First pass: one claim per timeline
    for tl in sorted_tls:
        if counters["fact"] >= targets["fact"]:
            break
        cv = tl.current_value()
        if not cv:
            continue
        text = _make_fact_text(tl.subject, tl.attribute, cv)
        form = {
            "subject": tl.subject,
            "attribute": tl.attribute,
            "value": cv,
        }
        conf = confidence_for(tl)
        add_claim("fact", text, form, conf)

    # Second pass: alternate phrasings for remaining slots
    if counters["fact"] < targets["fact"]:
        # More template variants
        alt_templates = [
            lambda s, a, v, r: f"{s} currently has {r}.",
            lambda s, a, v, r: f"{s} reports {r} for {attr_to_words(a)}.",
            lambda s, a, v, r: f"According to reports, {s} has {r}.",
            lambda s, a, v, r: f"{s} shows {r} as its {attr_to_words(a)}.",
            lambda s, a, v, r: f"The {attr_to_words(a)} for {s} stands at {r}.",
            lambda s, a, v, r: f"{s} is known to have {r}.",
            lambda s, a, v, r: f"For {s}, the {attr_to_words(a)} is {r}.",
        ]
        for tl in sorted_tls:
            if counters["fact"] >= targets["fact"]:
                break
            cv = tl.current_value()
            if not cv:
                continue
            rendered = render_value(cv)
            for tmpl in alt_templates:
                if counters["fact"] >= targets["fact"]:
                    break
                try:
                    text = tmpl(tl.subject, tl.attribute, cv, rendered)
                except Exception:
                    continue
                if len(text) > 300:
                    continue
                # Don't use templates that have numbers for booleans
                if cv.get("kind") == "boolean":
                    continue
                form = {
                    "subject": tl.subject,
                    "attribute": tl.attribute,
                    "value": cv,
                }
                add_claim("fact", text, form, confidence_for(tl))

    # ---- Fill any remaining gaps ----
    # If any type is short, fill with facts
    total = sum(counters.values())
    while total < 1000:
        # Generate more fact variants
        for tl in sorted_tls:
            if total >= 1000:
                break
            cv = tl.current_value()
            if not cv:
                continue
            rendered = render_value(cv)
            if cv.get("kind") == "boolean":
                continue
            # Additional fallback templates
            fallback_texts = [
                f"As of the latest update, {tl.subject} has {rendered}.",
                f"{tl.subject} records {rendered} for {attr_to_words(tl.attribute)}.",
                f"The {attr_to_words(tl.attribute)} of {tl.subject} is recorded as {rendered}.",
                f"{tl.subject} maintains {rendered} for {attr_to_words(tl.attribute)}.",
            ]
            for text in fallback_texts:
                if total >= 1000:
                    break
                if len(text) > 300:
                    continue
                form = {
                    "subject": tl.subject,
                    "attribute": tl.attribute,
                    "value": cv,
                }
                if add_claim("fact", text, form, confidence_for(tl)):
                    total += 1

    # Truncate to exactly 1000 if over
    if len(claims) > 1000:
        claims = claims[:1000]

    return claims
