import re
from typing import Dict, List, Pattern

# Tier-0 Hard Refusal Responses
REFUSAL_MESSAGES: Dict[str, str] = {
    "emergency": (
        "CRITICAL SAFETY REFUSAL: The query describes symptoms that may indicate a medical emergency "
        "(e.g., severe pain, breathing distress, stroke symptoms, loss of consciousness, or hemorrhage). "
        "AyurCite does not handle acute emergencies. Please call emergency services (e.g., 911 / 112 / 108) "
        "or proceed immediately to the nearest emergency department."
    ),
    "self_harm": (
        "CRITICAL SAFETY REFUSAL: If you or someone you know is experiencing distress or thoughts of self-harm, "
        "please reach out immediately to a crisis lifeline (e.g., call or text 988 in North America, "
        "or contact local mental health emergency helplines)."
    ),
    "pregnancy": (
        "SAFETY REFUSAL: AyurCite strictly prohibits recommendations or dosing guidance during pregnancy or "
        "lactation. Many classical herbs induce uterine contractions or hormonal fluctuations. "
        "Consult an OB-GYN and a licensed Ayurvedic physician."
    ),
    "pediatric": (
        "SAFETY REFUSAL: AyurCite strictly prohibits pediatric dosing or treatments for infants and young children. "
        "Pediatric pharmacodynamics require in-person clinical supervision by a certified pediatrician."
    ),
    "oncology": (
        "SAFETY REFUSAL: AyurCite refuses queries seeking cures or direct treatment protocols for cancer or malignant "
        "neoplasms. Oncology requires evidence-based medical oncology care. Consult your oncologist."
    ),
    "medication_replacement": (
        "SAFETY REFUSAL: AyurCite strictly refuses guidance on discontinuing, tapering, or replacing prescribed "
        "pharmaceutical medications with herbal substitutes. Altering prescribed therapy without consulting your "
        "prescribing physician can cause fatal complications."
    ),
    "bhasma_rasashastra": (
        "SAFETY REFUSAL: AyurCite does not index or provide instructions on Rasa Shastra, bhasma preparation, "
        "or heavy metal / mineral compounds (mercury, arsenic, lead, copper). Home preparation or unregulated "
        "consumption poses severe toxicity risks."
    ),
}

# Compiled regexes for ultra-fast Tier-0 checking (<5ms)
SAFETY_PATTERNS: Dict[str, List[Pattern]] = {
    "emergency": [
        re.compile(r"\b(chest\s*pain|heart\s*attack|cardiac\s*arrest|shortness\s*of\s*breath|difficulty\s*breathing|cannot\s*breathe)\b", re.I),
        re.compile(r"\b(arterial\s*bleed(ing)?|(severe|profuse)\s*bleed(ing)?|hemorrhage|unconscious(ness)?|fainted|passed\s*out|anaphylaxis|stroke|slurred\s*speech|facial\s*droop)\b", re.I),
        re.compile(r"\b(seizure(s)?|convuls(ing|ion|ions)|coughing\s*up\s*blood|vomiting\s*blood)\b", re.I),
    ],
    "self_harm": [
        re.compile(r"\b(suicid(e|al)|kill\s*myself|end\s*my\s*life|want\s*to\s*die|self[-\s]*harm|overdose\s*(on|to\s*die))\b", re.I),
    ],
    "pregnancy": [
        re.compile(r"\b(pregnant|pregnancy|first\s*trimester|second\s*trimester|third\s*trimester|lactati(ng|on)|breastfeeding|nursing\s*(mother|mom)?)\b.*\b(dose|dosage|cure|remedy|take|drink|herb|medicine|safe)\b", re.I),
        re.compile(r"\b(dose|dosage|safe\s*to\s*take|can\s*i\s*take|take|remedy)\b.*\b(during\s*pregnancy|while\s*pregnant|for\s*pregnant|breastfeeding|trimester|lactation|nursing\s*(mother|mom)?)\b", re.I),
        re.compile(r"\b(abortifacient|induce\s*abortion|induce\s*miscarriage)\b", re.I),
    ],
    "pediatric": [
        re.compile(r"\b(dose|dosage|how\s*much|drops|give|administer)\b.*\b(infant|baby|newborn|toddler|child|kid|1\s*year\s*old|2\s*year\s*old)\b", re.I),
        re.compile(r"\b(infant|baby|toddler|pediatric|child|kid)\b.*\b(dose|dosage|cure|treatment|drops)\b", re.I),
    ],
    "oncology": [
        re.compile(r"\b(cure|treat|shrink|reverse)\b.*\b(cancer|tumor|tumour|carcinoma|sarcoma|leukemia|lymphoma|melanoma|oncology|glioblastoma)\b", re.I),
        re.compile(r"\b(cancer|tumor|tumour|carcinoma|leukemia|glioblastoma)\b.*\b(cure|herbal\s*cure|ayurvedic\s*cure|natural\s*cure|shrink)\b", re.I),
    ],
    "medication_replacement": [
        re.compile(r"\b(stop|quit|replace|substitute|wean\s*off|discontinue)\b.*\b(metformin|insulin|statin|atorvastatin|lisinopril|amlodipine|losartan|blood\s*pressure\s*med|bp\s*med|antidepressant|ssri|chemo|thyroxine|levothyroxine|warfarin|blood\s*thinner)\b", re.I),
        re.compile(r"\b(herbal|ayurvedic)\s*alternative\s*to\s*(replace|stop)\b", re.I),
    ],
    "bhasma_rasashastra": [
        re.compile(r"\b(bhasma|rasashastra|rasa\s*shastra|parada|kajjali|calcined\s*mercury|purif(y|ied)\s*mercury|arsenic\s*bhasma|swarna\s*bhasma|calx|tamra\s*bhasma|naga\s*bhasma|haratala)\b", re.I),
        re.compile(r"\bhow\s*to\s*(make|prepare|burn|calcine)\b.*\b(bhasma|mercury|lead|arsenic)\b", re.I),
    ],
}

# Tier-1: Modern pharmaceutical drug names to flag for potential herb-drug interaction
COMMON_PHARMA_DRUGS = {
    "warfarin", "aspirin", "clopidogrel", "heparin", "apixaban", "rivaroxaban",
    "metformin", "glipizide", "insulin",
    "lisinopril", "amlodipine", "losartan", "metoprolol", "atorvastatin", "simvastatin",
    "levothyroxine", "synthroid",
    "sertraline", "fluoxetine", "escitalopram", "duloxetine", "alprazolam", "clonazepam",
    "methotrexate", "prednisone", "cyclosporine", "tacrolimus", "phenytoin", "carbamazepine",
    "lithium", "digoxin"
}
