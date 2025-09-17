import re
import unicodedata
from app.core.constants import ALIASES
from typing import Any, List, Mapping, Tuple, Optional
from rapidfuzz import fuzz

# --- Normalization helper functions ------------------------------------------------------------------

WORD_RE = re.compile(r"[^\w\s]+", flags=re.UNICODE)

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def normalize(s: str) -> str:
    s = s.lower().strip()               # lowercase + trim
    s = strip_accents(s)               # remove accents (NFKD)
    s = WORD_RE.sub(" ", s)       # remove punctuation
    s = " ".join(s.split())             # collapse spaces
    # Use aliases to convert bad word into mapping right word using _ALIASES dict
    for bad, good in ALIASES.items():
        s = re.sub(rf"\b{re.escape(bad)}\b", good, s)
    return s

def tokens(s: str) -> List[str]:
    return normalize(s).split()

# --- Scoring ------------------------------------------------------------------

def composite_score(desc_norm: str, query_norm: str) -> float:
    """Weighted composite score using RapidFuzz metrics."""
    s1 = fuzz.WRatio(desc_norm, query_norm)          # holistic
    s2 = fuzz.token_set_ratio(desc_norm, query_norm) # unordered token overlap
    s3 = fuzz.partial_ratio(desc_norm, query_norm)   # handles substrings
    return 0.5 * s1 + 0.3 * s2 + 0.2 * s3

# --- Nutrition extraction -----------------------------------------------------

def find_energy_kcal(food: Mapping[str, Any]) -> Tuple[Optional[float], str]:
    label = food.get("labelNutrients") or {}
    if isinstance(label, dict):
        cal = label.get("calories")
        if isinstance(cal, dict) and isinstance(cal.get("value"), (int, float)):
            return float(cal["value"]), "per serving (label)"

    for n in (food.get("foodNutrients") or []):
        name = (n.get("nutrientName") or "").lower()
        unit = (n.get("unitName") or "").lower()
        val = n.get("value")
        if not isinstance(val, (int, float)):
            continue
        if "energy" in name:
            if unit in ("kcal", "kcals"):
                return float(val), "per 100 g"
            if unit in ("kj", "kilojoules"):
                return float(val) / 4.184, "per 100 g(converted from kJ)"
    return None, ""

def serving_grams(food: Mapping[str, Any]) -> Optional[float]:
    size = food.get("servingSize")
    unit = (food.get("servingSizeUnit") or "").lower()
    if isinstance(size, (int, float)) and unit in ("g", "gram", "grams"):
        return float(size)
    return None

