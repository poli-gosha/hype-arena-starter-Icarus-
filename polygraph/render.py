"""Value renderer for Polygraph claim generator."""

CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£"}

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Attribute name overrides
ATTR_OVERRIDES = {
    "cto": "CTO",
    "ceo": "CEO",
    "coo": "COO",
    "cpo": "CPO",
    "cso": "CSO",
    "vp_engineering": "VP Engineering",
    "vp_product": "VP Product",
    "vp_sales": "VP Sales",
    "vp_marketing": "VP Marketing",
    "soc2_certified": "SOC 2 certified",
    "soc2": "SOC 2",
    "gdpr": "GDPR",
    "api": "API",
    "saml": "SAML",
    "sso": "SSO",
    "ai_sidebar": "AI sidebar",
    "ai_search": "AI search",
    "ai_suggestions": "AI suggestions",
}


def render_date(d: str) -> str:
    """2026-03-12 -> '12 March 2026', 2026-03 -> 'March 2026', 2026 -> '2026'"""
    parts = d.split("-")
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        year, month = parts
        return f"{MONTH_NAMES[int(month)]} {year}"
    else:
        year, month, day = parts
        return f"{int(day)} {MONTH_NAMES[int(month)]} {year}"


def render_quantity(v, unit: str) -> str:
    """12, 'language' -> '12 languages'; 10000, 'customer' -> '10,000 customers'"""
    # Format number with commas for thousands
    if isinstance(v, float) and v == int(v):
        v = int(v)
    num_str = f"{v:,}" if isinstance(v, int) else f"{v:,.2f}".rstrip("0").rstrip(".")
    # Pluralize
    plural = _pluralize(unit)
    return f"{num_str} {plural}"


def _pluralize(unit: str) -> str:
    """Simple pluralization."""
    special = {
        "person": "people",
        "company": "companies",
        "country": "countries",
        "city": "cities",
        "category": "categories",
        "query": "queries",
        "entry": "entries",
        "delivery": "deliveries",
        "activity": "activities",
        "min": "minutes",
        "minute": "minutes",
        "hour": "hours",
        "day": "days",
        "week": "weeks",
        "month": "months",
        "year": "years",
        "second": "seconds",
    }
    if unit in special:
        return special[unit]
    if unit.endswith("s"):
        return unit
    if unit.endswith("y") and len(unit) > 1 and unit[-2] not in "aeiou":
        return unit[:-1] + "ies"
    if unit.endswith("sh") or unit.endswith("ch") or unit.endswith("x"):
        return unit + "es"
    return unit + "s"


def render_money(v, currency: str, per: str = None) -> str:
    """59, 'EUR', 'month' -> '€59 per month'"""
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if isinstance(v, float) and v == int(v):
        v_str = str(int(v))
    else:
        v_str = f"{v:.2f}".rstrip("0").rstrip(".")
    base = f"{symbol}{v_str}"
    if per:
        return f"{base} per {per}"
    return base


def render_value(value: dict) -> str:
    """Render a value dict to its canonical text form."""
    kind = value.get("kind")
    if kind == "money":
        return render_money(value["value"], value["currency"], value.get("per"))
    elif kind == "quantity":
        return render_quantity(value["value"], value["unit"])
    elif kind == "date":
        return render_date(value["value"])
    elif kind == "duration":
        v = value["value"]
        unit = value["unit"]
        if isinstance(v, float) and v == int(v):
            v = int(v)
        return f"{v} {_pluralize(unit)}"
    elif kind == "percent":
        v = value["value"]
        if isinstance(v, float) and v == int(v):
            v_str = str(int(v))
        else:
            v_str = f"{v:g}"
        return f"{v_str}%"
    elif kind == "version":
        ver = value["value"]
        # Only add v prefix for simple major.minor (not patch versions)
        parts = ver.split(".")
        if len(parts) == 2:
            return f"v{ver}"
        return ver
    elif kind == "boolean":
        return "true" if value["value"] else "false"
    elif kind == "name":
        return value["value"]
    else:
        return str(value)


def attr_to_words(attribute: str) -> str:
    """Convert attribute name to readable words.
    cto -> 'CTO'
    series_a_lead -> 'Series A lead'
    head_of_product -> 'head of product'
    soc2_certified -> 'SOC 2 certified'
    """
    if attribute in ATTR_OVERRIDES:
        return ATTR_OVERRIDES[attribute]
    # Replace underscores with spaces
    words = attribute.split("_")
    result_words = []
    for w in words:
        if w in ATTR_OVERRIDES:
            result_words.append(ATTR_OVERRIDES[w])
        elif w.lower() in ("a", "an", "the", "of", "in", "at", "by", "for", "and", "or"):
            result_words.append(w.lower())
        elif w.upper() in ("CEO", "CTO", "COO", "CPO", "VP", "API", "SOC2", "SOC", "GDPR", "AI", "SSO", "SAML"):
            result_words.append(w.upper())
        else:
            result_words.append(w.lower())
    return " ".join(result_words)
