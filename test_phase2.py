"""
Unit and Integration Tests for Phase 2 Tasks (2A, 2B, 2C, 2D).
"""

import os
import unittest
import pandas as pd
from validation import evaluate_baselines, CORE_TARGETS
from resource_hunter import PASS_DEFINITIONS, reconstruct_abstract
from lens_harvester import (
    build_lens_query,
    map_patent_to_16_col,
    harvest_patents,
    MOCK_LENS_RESPONSE,
    TARGET_IPC_CLASSES
)
from fleet_harvester import (
    clean_and_parse_json,
    map_fleet_json_to_16_col,
    harvest_fleet_data,
    DEFAULT_QUERIES
)


class TestPhase2Validation(unittest.TestCase):
    def test_empty_dataframe(self):
        res = evaluate_baselines(pd.DataFrame())
        self.assertEqual(res["matched_count"], 0)
        self.assertEqual(res["total_targets"], 4)

    def test_manual_rows_not_counted(self):
        df = pd.DataFrame([
            {"Item": "PureBilge Compact", "Company or publisher": "Alfa Laval", "Found by": "Manual"},
            {"Item": "MiniBOSS", "Company or publisher": "Wave International", "Found by": "Manual"},
            {"Item": "BISEP19", "Company or publisher": "Vetus", "Found by": "Manual"},
            {"Item": "US5277797A", "Company or publisher": "US patent", "Found by": "Manual"}
        ])
        res = evaluate_baselines(df)
        self.assertEqual(res["matched_count"], 0)

    def test_script_rows_matched(self):
        df = pd.DataFrame([
            {"Item": "Compact PureBilge Unit", "Company or publisher": "Alfa Laval", "Found by": "Script"},
            {"Item": "MiniBOSS OWS System", "Company or publisher": "Wave International", "Found by": "Script"},
            {"Item": "BISEP19 Filter", "Company or publisher": "Vetus", "Found by": "Script"},
            {"Item": "US5277797A Separator", "Company or publisher": "Inventor", "Found by": "Script"},
        ])
        res = evaluate_baselines(df)
        self.assertEqual(res["matched_count"], 4)
        for target in CORE_TARGETS:
            self.assertTrue(res["details"][target["name"]])

    def test_partial_match(self):
        df = pd.DataFrame([
            {"Item": "Generic separator", "Company or publisher": "Alfa Laval", "Found by": "Script"},
            {"Item": "Other boat item", "Company or publisher": "Other Co", "Found by": "Script"}
        ])
        res = evaluate_baselines(df)
        self.assertEqual(res["matched_count"], 1)
        self.assertTrue(res["details"]["Alfa Laval / PureBilge"])
        self.assertFalse(res["details"]["Wave International / MiniBOSS"])


class TestPhase2OpenAlex(unittest.TestCase):
    def test_pass_definitions(self):
        self.assertEqual(len(PASS_DEFINITIONS), 3)
        self.assertIn("tanker", PASS_DEFINITIONS[1]["exclusions"])
        self.assertIn("cargo ship", PASS_DEFINITIONS[1]["exclusions"])
        self.assertIn("offshore platform", PASS_DEFINITIONS[1]["exclusions"])

    def test_abstract_reconstruction(self):
        inv_index = {"hello": [0], "world": [1]}
        self.assertEqual(reconstruct_abstract(inv_index), "hello world")
        self.assertEqual(reconstruct_abstract(None), "")


class TestPhase2LensPatent(unittest.TestCase):
    def test_query_ipc_filters(self):
        query = build_lens_query()
        must_clauses = query["query"]["bool"]["must"]
        ipc_filter = must_clauses[1]["terms"]["classification_ipcr.symbol"]
        self.assertEqual(set(ipc_filter), set(TARGET_IPC_CLASSES))

    def test_mock_patent_harvest_and_validation(self):
        test_csv = "data/test_patent_suite.csv"
        try:
            harvest_patents(csv_path=test_csv)
            df = pd.read_csv(test_csv)
            self.assertGreaterEqual(len(df), 4)
            # Ensure US5277797A is present
            matches = df[df["Item"].str.contains("US5277797A", case=False)]
            self.assertFalse(matches.empty)
            # Evaluate with Paul Check
            val = evaluate_baselines(df)
            self.assertEqual(val["matched_count"], 4)
        finally:
            if os.path.exists(test_csv):
                os.remove(test_csv)


class TestPhase2FleetPerplexity(unittest.TestCase):
    def test_json_cleaner(self):
        raw = """```json
        {
            "Figure": "370,000",
            "Unit": "boats",
            "Country": "Germany",
            "Company or publisher": "Federal Ministry"
        }
        ```"""
        parsed = clean_and_parse_json(raw)
        self.assertEqual(parsed["Figure"], "370,000")
        self.assertEqual(parsed["Unit"], "boats")
        self.assertEqual(parsed["Country"], "Germany")
        self.assertEqual(parsed["Company or publisher"], "Federal Ministry")

    def test_harvest_fleet_mock(self):
        test_csv = "data/test_fleet_suite.csv"
        try:
            harvest_fleet_data(queries=DEFAULT_QUERIES, csv_path=test_csv)
            df = pd.read_csv(test_csv)
            self.assertEqual(len(df), 2)
            self.assertEqual(df["Category"].iloc[0], "Fleet")
            self.assertEqual(df["Found by"].iloc[0], "Script")
            self.assertIn("370,000", df["Figure"].values)
        finally:
            if os.path.exists(test_csv):
                os.remove(test_csv)


if __name__ == "__main__":
    unittest.main()
