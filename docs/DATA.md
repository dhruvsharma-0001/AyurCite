# AyurCite Data Provenance & Licensing Stance

In health and legal AI systems, data licensing is the foundational bottleneck, not data availability.

---

## 1. The Licensing Dilemma in Ayurvedic NLP

While ancient Sanskrit texts are thousands of years old and in the public domain, modern English translations, commentaries, and typographical arrangements are often under active commercial copyright (e.g., Chaukhamba editions from the 1990s).

### AyurCite Policy:
1. **Verifiable Public Domain Only**: We restrict texts to verified editions published prior to 1928, whose copyright has expired worldwide.
2. **Strict License Ledger**: Every document ingested is tracked in `data/license_ledger.csv`.
3. **Reproducible Acquisition**: We never redistribute raw book scans or copyrighted text files. Users reproduce the raw corpus on their own machine via `scripts/01_acquire.py`.

---

## 2. Ingested Editions

| Document ID | Title | Author | Translator | Year | Publisher | License Verdict | Status |
|---|---|---|---|---|---|---|---|
| `cs_kaviratna_1890` | Charaka-Samhita (Sutrasthana) | Agnivesha / Charaka | Kaviraj Avinash Chandra Kaviratna | 1890 | Calcutta (D.C. Dass & Co.) | Public Domain (pre-1928) | Ingested |
| `ss_bhishagratna_1907` | Sushruta Samhita Vol 1 (Sutrasthana) | Sushruta | Kaviraj Kunja Lal Bhishagratna | 1907 | Calcutta | Public Domain (pre-1928) | Ingested |
| `niimh_ecaraka_sutra` | Charaka Samhita Sutrasthana e-Samhita | Agnivesha / Charaka | — | 2020 | NIIMH / CCRAS Ministry of Ayush | Public Reference | Tracked |
| `wisdomlib_charaka` | Charaka Samhita Online Edition | Agnivesha / Charaka | — | 2021 | Wisdomlib | Shadow Entry | Excluded |

---

## 3. Cryptographic Integrity

All source documents downloaded by `scripts/01_acquire.py` are verified against SHA256 hashes recorded in `data/manifest.json`:

```json
{
  "doc_id": "cs_kaviratna_1890",
  "sha256": "f279e9499b6cc31a39d5498bb2da3e659bdbdac5ef753114ce5ccf76c2c8c673",
  "bytes": 4989688
},
{
  "doc_id": "ss_bhishagratna_1907",
  "sha256": "73655aa11aa38eb6224415ab90a842f66e96c10785a0cb5c64abc335c9a16f17",
  "bytes": 1103574
}
```

---

## 4. Verse Identification Scheme

To enable cross-verification with physical books, AyurCite segments the corpus into verse units with a permanent, human-readable identifier:

```
<compendium>_<sthana>_<chapter>_<verse>
```

- `cs_su_01_015` → Charaka Samhita, Sutrasthana, Chapter 1, Verse 15
- `ss_su_15_041` → Sushruta Samhita, Sutrasthana, Chapter 15, Verse 41
