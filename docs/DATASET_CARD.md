# Dataset Card: AyurCite Classical Verse Corpus

## Dataset Description
- **Curated By**: AyurCite Project Contributors
- **Language**: English translations with Romanized Sanskrit (IAST) terms
- **Domain**: Classical Ayurvedic literature (Ayurveda Samhitas)
- **Size**: 5,905 verse units across 76 chapters

## Sub-Collections
1. **Charaka Samhita (Sutrasthana)**:
   - Chapters: 1 to 30 (30 Adhyayas)
   - Verses: 5,169 records
   - Source: Translation by Kaviraj Avinash Chandra Kaviratna (1890, Calcutta)
   - License: Public Domain (published before 1928)
2. **Sushruta Samhita (Sutrasthana)**:
   - Chapters: 1 to 46 (46 Adhyayas)
   - Verses: 736 records
   - Source: Translation by Kaviraj Kunja Lal Bhishagratna (1907, Calcutta)
   - License: Public Domain (published before 1928)

## Record Schema
```json
{
  "verse_id": "cs_su_01_015",
  "book": "Charaka Samhita",
  "sthana": "Sutrasthana",
  "chapter": 1,
  "chapter_title": "Deerghanjiviteeya Adhyaya",
  "verse": 15,
  "sanskrit_iast": "...",
  "english": "...",
  "translator": "Avinash Chandra Kaviratna",
  "edition_year": 1890,
  "doc_id": "cs_kaviratna_1890",
  "topics": ["dosha", "vata"],
  "entities": {
    "herbs": ["haritaki"],
    "conditions": ["amlapitta"]
  },
  "prev_verse_id": "cs_su_01_014",
  "next_verse_id": "cs_su_01_016"
}
```

## Licensing & Provenance
All source texts are verified public domain. Cryptographic hashes and acquisition manifests are recorded in `data/manifest.json` and `data/license_ledger.csv`.
