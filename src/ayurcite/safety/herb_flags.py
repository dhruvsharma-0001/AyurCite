import csv
from pathlib import Path

from pydantic import BaseModel


class HerbFlagRecord(BaseModel):
    herb_canonical: str
    botanical_name: str
    flag_category: str
    flag_note: str
    source_citation: str
    source_url: str
    date_checked: str


class HerbFlagRegistry:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.flags: list[HerbFlagRecord] = []
        self._load()

    def _load(self):
        if not self.csv_path.exists():
            return
        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.flags.append(HerbFlagRecord(**row))

    def find_flags_for_herb(self, herb_name: str) -> list[HerbFlagRecord]:
        h_norm = herb_name.strip().lower()
        return [
            flag
            for flag in self.flags
            if h_norm in flag.herb_canonical.lower() or h_norm in flag.botanical_name.lower()
        ]

    def scan_query(self, query: str) -> list[HerbFlagRecord]:
        q_norm = query.lower()
        matched = []
        seen_keys = set()
        for flag in self.flags:
            if flag.herb_canonical.lower() in q_norm or flag.botanical_name.lower() in q_norm:
                key = (flag.herb_canonical, flag.flag_category)
                if key not in seen_keys:
                    seen_keys.add(key)
                    matched.append(flag)
        return matched
