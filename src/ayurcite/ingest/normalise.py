import unicodedata
from typing import Dict, List, Set

# Botanical & Classical Terminology Normalization Map (NAMASTE / NAMC / IMPPAT aligned)
CANONICAL_TERM_MAP: Dict[str, List[str]] = {
    "haritaki": ["haritaki", "harad", "harada", "harītakī", "chebulic myrobalan", "terminalia chebula", "abhaya", "pathya"],
    "amalaki": ["amalaki", "amla", "āmalakī", "indian gooseberry", "emblica officinalis", "phyllanthus emblica", "dhatri"],
    "bibhitaki": ["bibhitaki", "baheda", "belleric myrobalan", "terminalia bellirica", "vibhītaka", "akṣa"],
    "triphala": ["triphala", "three myrobalans", "trifala", "triphalā"],
    "ashwagandha": ["ashwagandha", "asgandh", "aśvagandhā", "withania somnifera", "winter cherry", "indian ginseng"],
    "guggulu": ["guggulu", "guggul", "commiphora mukul", "commiphora wightii", "indian bdellium"],
    "yashtimadhu": ["yashtimadhu", "mulethi", "licorice", "liquorice", "glycyrrhiza glabra", "yaṣṭimadhu", "madhuka"],
    "brahmi": ["brahmi", "brāhmī", "bacopa monnieri", "water hyssop"],
    "shatavari": ["shatavari", "satavar", "śatāvarī", "asparagus racemosus"],
    "tulsi": ["tulsi", "tulasi", "holy basil", "ocimum sanctum", "ocimum tenuiflorum"],
    "haridra": ["haridra", "haldi", "turmeric", "curcuma longa", "haridrā", "nisha"],
    "guduchi": ["guduchi", "giloy", "tinospora cordifolia", "guḍūcī", "amrita"],
    "nimba": ["nimba", "neem", "azadirachta indica", "margosa"],
    "shallaki": ["shallaki", "salai", "boswellia serrata", "indian frankincense"],
    "kutki": ["kutki", "katuka", "picrorhiza kurroa", "kaṭurohiṇī"],
    "vata": ["vata", "vātá", "vayu", "vāyu", "wind humor"],
    "pitta": ["pitta", "bile humor", "agni"],
    "kapha": ["kapha", "shleshma", "śleṣman", "phlegm humor"],
    "ojas": ["ojas", "vital essence", "balam"],
    "ama": ["ama", "āma", "metabolic toxin", "undigested food"],
    "agni": ["agni", "digestive fire", "jatharagni", "jaṭharāgni"],
    "dinacharya": ["dinacharya", "dinacaryā", "daily regimen", "daily routine"],
    "ritucharya": ["ritucharya", "ṛtucaryā", "seasonal regimen", "seasonal routine"],
}

# Inverted index: variant -> canonical term
VARIANT_TO_CANONICAL: Dict[str, str] = {}
for canonical, variants in CANONICAL_TERM_MAP.items():
    for var in variants:
        VARIANT_TO_CANONICAL[var.lower()] = canonical

def strip_accents_iast(text: str) -> str:
    """Normalize IAST characters (ā -> a, ī -> i, ū -> u, ṛ -> r, etc.)."""
    # Decompose unicode characters, strip diacritical marks
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def expand_query_terms(query: str) -> List[str]:
    """
    Expand query terms using the canonical terminology layer:
    e.g. 'harad' -> ['harad', 'haritaki', 'harītakī', 'chebulic myrobalan', 'terminalia chebula', ...]
    """
    q_lower = query.lower()
    expanded_terms: Set[str] = set()

    for variant, canonical in VARIANT_TO_CANONICAL.items():
        if variant in q_lower:
            for syn in CANONICAL_TERM_MAP[canonical]:
                expanded_terms.add(syn)
                expanded_terms.add(strip_accents_iast(syn))

    return sorted(list(expanded_terms))

def get_canonical_term(term: str) -> str:
    """Return the canonical term for a given synonym/variant, or stripped input if unknown."""
    norm = term.strip().lower()
    return VARIANT_TO_CANONICAL.get(norm, strip_accents_iast(norm))
