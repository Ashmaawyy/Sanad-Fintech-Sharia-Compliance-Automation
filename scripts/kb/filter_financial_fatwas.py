"""Filter the fatwa corpus to finance-related inquiries.

The classifier is intentionally conservative and question-led. Run without
``--apply`` for a report; ``--apply`` replaces the CSV after creating a
backup and writes retained source row indices for aligned embedding slicing.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "data_archive" / "fiqh" / "financial_qa" / "financial_fatwas.csv"
BACKUP_PATH = PROJECT_ROOT / "data_archive" / "sources" / "fatwas" / "islamic_qa_full.csv"
INDEX_PATH = PROJECT_ROOT / "data_archive" / "derived" / "fiqh" / "financial_fatwas_source_row_indices.txt"


def normalize(text: str) -> str:
    """Normalize Arabic spelling and whitespace for matching only."""
    text = text.casefold()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", text).strip()


STRONG_PATTERNS: tuple[tuple[str, str], ...] = (
    ("riba", r"(?:^|\s)(?:ال)?(?:ربا|ربوي(?:ه)?)(?:\s|$)"),
    ("loan", r"(?:ال)?قرض\w*|(?:ال)?اقتراض\w*|(?:ال)?مقترض\w*|(?:ال)?مقرض\w*"),
    ("banking", r"(?:ال)?بنك\w*|(?:ال)?بنوك\w*|(?:ال)?مصرف\w*|(?:ال)?مصارف\w*"),
    ("murabaha", r"(?:ال)?مرابحه\w*"),
    ("mudarabah", r"(?:ال)?مضاربه\w*"),
    ("partnership", r"(?:ال)?شراكه\w*|(?:ال)?مشاركه\s+(?:متناقصه|في\s+(?:راس المال|شركه))"),
    ("manufacturing_sale", r"(?:ال)?استصناع\w*"),
    ("currency", r"\bعملات\w*\b|\bصرف العملات\b|\bعمله\s+(?:اجنبيه|محليه|ورقيه|ذهبيه|فضيه)"),
    ("stocks", r"(?:ال)?اسهم\w*|(?:ال)?بورصه\w*"),
    ("interest", r"(?:ال)?فائده\w*|(?:ال)?فوائد\w*"),
    ("investment", r"(?:ال)?استثمار\w*|رأس المال|راس المال"),
    ("trade", r"(?:ال)?تجار\w*|(?:ال)?تاجر\w*"),
    ("sale_purchase", r"(?:ال)?بيع\w*|(?:ال)?شراء\w*"),
    ("zakat", r"(?:ال)?زكاه\w*"),
)

CONTEXT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("gold_silver_money", r"\bذهب\w*\b|\bفضه\w*\b|\bنقود\w*\b|\bاموال\w*\b"),
    ("debt", r"\bدين\w*\b|\bديون\w*\b|\bدينه\w*\b"),
    ("profit_loss", r"\bربح\w*\b|\bارباح\w*\b|\bخسار\w*\b"),
    ("insurance", r"\bتامين\w*\b"),
    ("pledge_guarantee", r"\bرهن\w*\b|\bضمان\w*\b|\bكفاله\w*\b"),
    ("lease", r"\bاجاره\w*\b|\bاجار\w*\b"),
    ("salam", r"\bسلم\b"),
    ("endowment", r"\bوقف\w*\b"),
    ("inheritance", r"\bميراث\w*\b|\bارث\w*\b"),
)

EXCLUSIONS: tuple[str, ...] = (
    "تامين خلف الامام",
    "التامين خلف الامام",
    "سلم على النبي",
    "الصلاه على النبي",
    "ذهب الى",
    "ذهبنا الى",
    "صرف او عطف",
    "اداء عمله",
    "عمله يستوجب",
    "مشاركه النصارى",
    "مشاركه اليهود",
    "بيع واقتناء الحيوانات المحنطه",
    "شراء الجثث",
    "مقتضى البيعه",
)


def classify(question: str, answer: str = "") -> tuple[bool, tuple[str, ...]]:
    """Return whether an inquiry is financial and the matching categories."""
    text = normalize(question)
    if any(exclusion in text for exclusion in EXCLUSIONS):
        return False, ()

    matches = [name for name, pattern in STRONG_PATTERNS if re.search(pattern, text)]
    context = [name for name, pattern in CONTEXT_PATTERNS if re.search(pattern, text)]

    # Standalone generic words are not sufficient evidence of a financial query.
    if "zakat" in matches and not any(
        marker in text for marker in ("مال", "تجار", "اسهم", "ذهب", "فضه", "حلي", "نقود", "راتب", "دين")
    ):
        matches.remove("zakat")
    if "sale_purchase" in matches and not any(
        marker in text for marker in ("مال", "سلعه", "سعر", "تجار", "شراء", "بيع", "عقد", "سياره", "بيت", "ارض", "حيوان")
    ):
        matches.remove("sale_purchase")
    if "interest" in matches and "الصلاه" in text:
        matches.remove("interest")
    if "insurance" in context and "الصلاه" in text:
        context.remove("insurance")

    categories = tuple(dict.fromkeys(matches + context))
    return bool(matches or len(context) >= 2), categories


def process(apply: bool) -> tuple[int, int, Counter[str]]:
    """Write a filtered temporary file and optionally replace the source."""
    temp_path = CSV_PATH.with_suffix(".financial.tmp.csv")
    retained = 0
    total = 0
    categories: Counter[str] = Counter()
    indices: list[int] = []

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as source, temp_path.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(target, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        for row_number, row in enumerate(reader):
            total += 1
            keep, matched = classify(row.get("question", ""), row.get("answer", ""))
            if keep:
                writer.writerow(row)
                retained += 1
                indices.append(row_number)
                categories.update(matched)

    if apply:
        if not BACKUP_PATH.exists():
            shutil.copy2(CSV_PATH, BACKUP_PATH)
        temp_path.replace(CSV_PATH)
        INDEX_PATH.write_text("\n".join(map(str, indices)) + "\n", encoding="ascii")
    else:
        temp_path.unlink(missing_ok=True)

    return total, retained, categories


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="replace the CSV after creating a source backup")
    args = parser.parse_args()
    total, retained, categories = process(args.apply)
    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"{mode}: retained {retained:,} of {total:,} rows; removed {total - retained:,}")
    print("categories:", ", ".join(f"{key}={value}" for key, value in categories.most_common()))
    if args.apply:
        print(f"backup: {BACKUP_PATH}")
        print(f"row indices: {INDEX_PATH}")


if __name__ == "__main__":
    main()
