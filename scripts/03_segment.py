import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from src.ayurcite.ingest.schemas import VerseRecord
from src.ayurcite.ingest.normalise import CANONICAL_TERM_MAP, strip_accents_iast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_FILE = PROCESSED_DIR / "verses.jsonl"

ROMAN_NUMERAL_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18,
    "XIX": 19, "IXX": 19, "XX": 20, "XXI": 21, "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25,
    "XXVI": 26, "XXVII": 27, "XXVIII": 28, "XXIX": 29, "XXX": 30, "XXXI": 31, "XXXII": 32,
    "XXXIII": 33, "XXXIV": 34, "XXXV": 35, "XXXVI": 36, "XXXVII": 37, "XXXVIII": 38, "XXXIX": 39,
    "XL": 40, "XLI": 41, "XLII": 42, "XLIII": 43, "XLIV": 44, "XLV": 45, "XLVI": 46
}

CHARAKA_SUTRA_TITLES = {
    1: "Deerghanjiviteeya Adhyaya",
    2: "Apamarga Tanduliya Adhyaya",
    3: "Aragvadhiya Adhyaya",
    4: "Shadvirechana Shatashritiya Adhyaya",
    5: "Matrashiteeya Adhyaya",
    6: "Tasyashiteeya Adhyaya",
    7: "Navegandharaniya Adhyaya",
    8: "Indriyopakramaniya Adhyaya",
    9: "Khuddaka Chatushpada Adhyaya",
    10: "Maha Chatushpada Adhyaya",
    11: "Tisraishaniya Adhyaya",
    12: "Vatakalakaliya Adhyaya",
    13: "Snehadhyaya",
    14: "Svedadhyaya",
    15: "Upakalpaniya Adhyaya",
    16: "Chikitsaprabhritiya Adhyaya",
    17: "Kiyanta Shirasiya Adhyaya",
    18: "Trishothiya Adhyaya",
    19: "Ashtodariya Adhyaya",
    20: "Maharoga Adhyaya",
    21: "Ashtauninditiya Adhyaya",
    22: "Langhana Brimhaniya Adhyaya",
    23: "Santarpaniya Adhyaya",
    24: "Vidhashonitiya Adhyaya",
    25: "Yajjah Purushiya Adhyaya",
    26: "Atreyabhadrakapyiya Adhyaya",
    27: "Annapanavidhi Adhyaya",
    28: "Vividhashitapeeteeya Adhyaya",
    29: "Dashapranayataniya Adhyaya",
    30: "Arthedashamahamuliya Adhyaya",
}

SUSHRUTA_SUTRA_TITLES = {
    1: "Vedotpatti Adhyaya",
    2: "Shishyopanayaniya Adhyaya",
    3: "Adhyayanasampradaniya Adhyaya",
    4: "Prabhashaniya Adhyaya",
    5: "Agropaharaniya Adhyaya",
    6: "Ritucharya Adhyaya",
    7: "Yantravidhi Adhyaya",
    8: "Shastravacharaniya Adhyaya",
    9: "Yogyasutriya Adhyaya",
    10: "Vishikhanupreshaniya Adhyaya",
    11: "Kshara-paka-vidhi Adhyaya",
    12: "Agnikarma-vidhi Adhyaya",
    13: "Jalaukavacharaniya Adhyaya",
    14: "Shonitavarnaniya Adhyaya",
    15: "Doshadhatumalakshaya-vriddhi-vijnaniya Adhyaya",
    16: "Karnavyadha-bandhavidhi Adhyaya",
    17: "Amapakvaishaniya Adhyaya",
    18: "Vranalepana-bandhavidhi Adhyaya",
    19: "Vranitopapasaniya Adhyaya",
    20: "Hitahita Adhyaya",
    21: "Vranaprashna Adhyaya",
    22: "Vranasrava-vijnaniya Adhyaya",
    23: "Krityakritya-vidhi Adhyaya",
    24: "Vyadhisamuddeshiya Adhyaya",
    25: "Mishraka Adhyaya",
    26: "Pranashthashalya-vijnaniya Adhyaya",
    27: "Shalyoddharana Adhyaya",
    28: "Viparita-dutanirdeshaniya Adhyaya",
    29: "Viparitashakuna-vijnaniya Adhyaya",
    30: "Pancheyendriyartha-vijnaniya Adhyaya",
    31: "Chhayaviparita-vijnaniya Adhyaya",
    32: "Svabhavaviparita-vijnaniya Adhyaya",
    33: "Avaraniya Adhyaya",
    34: "Yuktaseniya Adhyaya",
    35: "Aturopakramaniya Adhyaya",
    36: "Bhumipravibhaga Adhyaya",
    37: "Mishraka Adhyaya",
    38: "Dravyasamgrahaniya Adhyaya",
    39: "Samshodhana-samshamaniya Adhyaya",
    40: "Dravya-rasa-guna-virya-vipaka-vijnaniya Adhyaya",
    41: "Dravyavisheshavijnaniya Adhyaya",
    42: "Rasa-vishesha-vijnaniya Adhyaya",
    43: "Vamanadravya-vikalpa-vijnaniya Adhyaya",
    44: "Virechanadravya-vikalpa-vijnaniya Adhyaya",
    45: "Dravadravya-vidhi Adhyaya",
    46: "Annapanavidhi Adhyaya"
}

def clean_ocr_text(text: str) -> str:
    """Remove header artifacts, normalize multiple spaces, remove OCR noise."""
    text = re.sub(r"Chap\.\s+[IVXLCDM0-9\.\s]+\]\s+SUTRASTHANAM\.?\s*\d*", "", text, flags=re.I)
    text = re.sub(r"\[\s*\d+\s*\]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    return text

def extract_entities_and_topics(text: str):
    lower = text.lower()
    topics = []
    herbs = []
    conditions = []

    for canonical, variants in CANONICAL_TERM_MAP.items():
        if any(v in lower for v in variants):
            if canonical in {"vata", "pitta", "kapha", "ojas", "ama", "agni", "dinacharya", "ritucharya"}:
                topics.append(canonical)
            else:
                herbs.append(canonical)

    if any(w in lower for w in ["fever", "jvara"]):
        conditions.append("jvara")
    if any(w in lower for w in ["diarrhea", "atisaara", "atisara"]):
        conditions.append("atisara")
    if any(w in lower for w in ["cough", "kasa"]):
        conditions.append("kasa")
    if any(w in lower for w in ["dyspnoea", "asthma", "shwasa", "svasa"]):
        conditions.append("shwasa")
    if any(w in lower for w in ["edema", "shotha", "oedema"]):
        conditions.append("shotha")

    return list(set(topics)), {"herbs": sorted(list(set(herbs))), "conditions": sorted(list(set(conditions)))}

def segment_charaka(raw_path: Path) -> List[VerseRecord]:
    with open(raw_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Sutrasthana ends before Vimanasthana (around line 29000)
    viman_idx = content.find("THE  PlM  OF  VI. MAN  AH")
    if viman_idx == -1:
        viman_idx = content.find("VIMAN")
    if viman_idx != -1:
        content = content[:viman_idx]

    lesson_pattern = re.compile(r"\n\s*LESSON\s+([IVXLCDM]+)[\.:\s]*\n", re.I)
    splits = lesson_pattern.split(content)

    records: List[VerseRecord] = []
    sthana = "Sutrasthana"
    sthana_code = "su"

    seen_chaps: Set[int] = set()
    for i in range(1, len(splits), 2):
        roman_num = splits[i].strip().upper()
        lesson_body = splits[i+1]
        chap_num = ROMAN_NUMERAL_MAP.get(roman_num, 1)

        if chap_num > 30 or chap_num in seen_chaps:
            continue
        seen_chaps.add(chap_num)

        title = CHARAKA_SUTRA_TITLES.get(chap_num, f"Lesson {chap_num}")
        cleaned = clean_ocr_text(lesson_body)

        raw_paras = [p.strip() for p in cleaned.split("\n\n") if len(p.strip()) > 20]
        verse_idx = 1
        for p in raw_paras:
            if p.startswith("*") or p.startswith("t ") or p.startswith("T "):
                continue
            words = p.split()
            if len(words) < 5:
                continue

            max_words = 350
            chunks = []
            if len(words) > max_words:
                for chunk_i in range(0, len(words), max_words):
                    sub = " ".join(words[chunk_i : chunk_i + max_words])
                    chunks.append(sub)
            else:
                chunks.append(p)

            for chunk_text in chunks:
                verse_id = f"cs_{sthana_code}_{chap_num:02d}_{verse_idx:03d}"
                topics, entities = extract_entities_and_topics(chunk_text)

                record = VerseRecord(
                    verse_id=verse_id,
                    book="Charaka Samhita",
                    sthana=sthana,
                    chapter=chap_num,
                    chapter_title=title,
                    verse=verse_idx,
                    english=chunk_text,
                    translator="Avinash Chandra Kaviratna",
                    edition_year=1890,
                    doc_id="cs_kaviratna_1890",
                    topics=topics,
                    entities=entities
                )
                records.append(record)
                verse_idx += 1

    return records

def segment_sushruta(raw_path: Path) -> List[VerseRecord]:
    with open(raw_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Find SUTRASTHANAM section
    sutra_pos = content.find("SUTRASTHANAM.")
    if sutra_pos != -1:
        content = content[sutra_pos:]

    chapter_pattern = re.compile(r"\n\s*CHAPTER\s+([IVXLCDM]+)[\.:\s]*\n", re.I)
    splits = chapter_pattern.split(content)

    records: List[VerseRecord] = []
    sthana = "Sutrasthana"
    sthana_code = "su"

    seen_chaps: Set[int] = set()
    for i in range(1, len(splits), 2):
        roman_num = splits[i].strip().upper()
        body = splits[i+1]
        chap_num = ROMAN_NUMERAL_MAP.get(roman_num, 1)

        if chap_num > 46 or chap_num in seen_chaps:
            continue
        seen_chaps.add(chap_num)

        title = SUSHRUTA_SUTRA_TITLES.get(chap_num, f"Chapter {chap_num}")
        cleaned = clean_ocr_text(body)

        raw_paras = [p.strip() for p in cleaned.split("\n\n") if len(p.strip()) > 20]
        verse_idx = 1
        for p in raw_paras:
            if p.startswith("*") or p.startswith("t ") or p.startswith("T "):
                continue
            words = p.split()
            if len(words) < 5:
                continue

            max_words = 350
            chunks = []
            if len(words) > max_words:
                for chunk_i in range(0, len(words), max_words):
                    sub = " ".join(words[chunk_i : chunk_i + max_words])
                    chunks.append(sub)
            else:
                chunks.append(p)

            for chunk_text in chunks:
                verse_id = f"ss_{sthana_code}_{chap_num:02d}_{verse_idx:03d}"
                topics, entities = extract_entities_and_topics(chunk_text)

                record = VerseRecord(
                    verse_id=verse_id,
                    book="Sushruta Samhita",
                    sthana=sthana,
                    chapter=chap_num,
                    chapter_title=title,
                    verse=verse_idx,
                    english=chunk_text,
                    translator="Kaviraj Kunja Lal Bhishagratna",
                    edition_year=1907,
                    doc_id="ss_bhishagratna_1907",
                    topics=topics,
                    entities=entities
                )
                records.append(record)
                verse_idx += 1

    return records

def link_neighbor_verses(records: List[VerseRecord]):
    """Link prev_verse_id and next_verse_id within the same chapter."""
    for i, rec in enumerate(records):
        if i > 0 and records[i-1].chapter == rec.chapter and records[i-1].book == rec.book:
            rec.prev_verse_id = records[i-1].verse_id
        if i < len(records) - 1 and records[i+1].chapter == rec.chapter and records[i+1].book == rec.book:
            rec.next_verse_id = records[i+1].verse_id

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cs_path = RAW_DIR / "cs_kaviratna_1890.txt"
    ss_path = RAW_DIR / "ss_bhishagratna_1907.txt"

    print("[Segment] Processing Charaka Samhita Sutrasthana...")
    cs_records = segment_charaka(cs_path)
    print(f"          Extracted {len(cs_records)} verses across 30 chapters.")

    print("[Segment] Processing Sushruta Samhita Sutrasthana...")
    ss_records = segment_sushruta(ss_path)
    print(f"          Extracted {len(ss_records)} verses across 46 chapters.")

    all_records = cs_records + ss_records
    print(f"[Segment] Total verses: {len(all_records)}. Linking context neighbors...")
    link_neighbor_verses(all_records)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(rec.model_dump_json() + "\n")

    print(f"[Segment] Successfully saved {len(all_records)} verses -> {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    main()
