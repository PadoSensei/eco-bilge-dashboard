"""
validation.py
=============
Baseline Validation Logic ("Paul Check") for EcoBilge Research Pipeline.

Evaluates whether automated scraping engines (Found by == 'Script')
have successfully identified Fina's 4 core targets:
1. Alfa Laval (or PureBilge)
2. Wave International (or MiniBOSS)
3. Vetus (or BISEP19)
4. US5277797A

Matching is case-insensitive across the 'Item' and 'Company or publisher' columns.
"""

from typing import Dict, Any, List
import pandas as pd

CORE_TARGETS = [
    {
        "name": "Alfa Laval / PureBilge",
        "patterns": ["alfa laval", "purebilge"]
    },
    {
        "name": "Wave International / MiniBOSS",
        "patterns": ["wave international", "miniboss"]
    },
    {
        "name": "Vetus / BISEP19",
        "patterns": ["vetus", "bisep19"]
    },
    {
        "name": "US5277797A",
        "patterns": ["us5277797a", "us5277797"]
    }
]


def evaluate_baselines(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Scans the 16-column DataFrame to check if automated results (Found by == 'Script')
    successfully found Fina's 4 core targets.

    Returns a dictionary containing:
      - 'matched_count': int (number of unique targets matched, 0-4)
      - 'total_targets': int (always 4)
      - 'details': dict mapping target name to boolean match status
      - 'matched_records': list of dicts with matching rows
    """
    total_targets = len(CORE_TARGETS)
    if df is None or df.empty or "Found by" not in df.columns:
        return {
            "matched_count": 0,
            "total_targets": total_targets,
            "details": {t["name"]: False for t in CORE_TARGETS},
            "matched_records": []
        }

    # Filter strictly for automated script rows
    script_df = df[df["Found by"].astype(str).str.strip().str.lower() == "script"].copy()

    details = {}
    matched_records = []
    matched_count = 0

    # Ensure required columns exist
    item_col = script_df["Item"].fillna("").astype(str).str.lower() if "Item" in script_df.columns else pd.Series([""] * len(script_df))
    company_col = script_df["Company or publisher"].fillna("").astype(str).str.lower() if "Company or publisher" in script_df.columns else pd.Series([""] * len(script_df))

    # Evaluate each target
    for target in CORE_TARGETS:
        patterns = target["patterns"]
        # Match if any pattern appears as a substring in Item OR Company or publisher
        mask = pd.Series([False] * len(script_df), index=script_df.index)
        for pat in patterns:
            pat_lower = pat.lower()
            mask = mask | item_col.str.contains(pat_lower, regex=False) | company_col.str.contains(pat_lower, regex=False)

        matched_rows = script_df[mask]
        is_matched = len(matched_rows) > 0
        details[target["name"]] = is_matched
        if is_matched:
            matched_count += 1
            for _, r in matched_rows.iterrows():
                rec = r.to_dict()
                rec["_matched_target"] = target["name"]
                matched_records.append(rec)

    return {
        "matched_count": matched_count,
        "total_targets": total_targets,
        "details": details,
        "matched_records": matched_records
    }
