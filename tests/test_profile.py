"""Unit tests for static and dynamic profile schemas, naming, and UOM consistency."""

from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tests.mock_udi import install_mock_udi_interface

install_mock_udi_interface()
import udiNetatmoLib as lib  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT_DIR / "profile"
UPPER_ALNUM_RE = re.compile(r"^[A-Z0-9]+$")


class TestProfileSchema(unittest.TestCase):
    def test_static_xml_ids_and_editors_are_uppercase_without_underscores(self):
        nodedef_root = ET.parse(PROFILE_DIR / "nodedef" / "nodedef.xml").getroot()
        editors_root = ET.parse(PROFILE_DIR / "editor" / "editors.xml").getroot()

        editor_ids = set()
        for ed in editors_root.findall(".//editor"):
            ed_id = ed.attrib.get("id", "")
            self.assertRegex(ed_id, UPPER_ALNUM_RE, f"Editor id '{ed_id}' must be uppercase alphanumeric")
            editor_ids.add(ed_id)
            for rng in ed.findall("./range"):
                nls = rng.attrib.get("nls")
                if nls is not None:
                    self.assertRegex(nls, UPPER_ALNUM_RE, f"Editor nls '{nls}' must be uppercase alphanumeric")

        for nd in nodedef_root.findall(".//nodeDef"):
            nd_id = nd.attrib.get("id", "")
            nls = nd.attrib.get("nls", "")
            self.assertRegex(nd_id, UPPER_ALNUM_RE, f"nodeDef id '{nd_id}' must be uppercase alphanumeric")
            self.assertRegex(nls, UPPER_ALNUM_RE, f"nodeDef nls '{nls}' must be uppercase alphanumeric")
            for st in nd.findall("./sts/st"):
                st_id = st.attrib.get("id", "")
                st_ed = st.attrib.get("editor", "")
                self.assertRegex(st_id, UPPER_ALNUM_RE)
                self.assertRegex(st_ed, UPPER_ALNUM_RE)
                self.assertIn(st_ed, editor_ids, f"State '{st_id}' references unknown editor '{st_ed}'")
            for param in nd.findall(".//accepts/cmd/p"):
                p_id = param.attrib.get("id", "")
                p_ed = param.attrib.get("editor", "")
                self.assertRegex(p_id, UPPER_ALNUM_RE)
                self.assertRegex(p_ed, UPPER_ALNUM_RE)
                self.assertIn(p_ed, editor_ids, f"Param '{p_id}' references unknown editor '{p_ed}'")

    def test_dynamic_profile_payload_structure_and_uom151_timestamp(self):
        payload_c = lib._dynamic_profile_payload("C")
        self.assertIn("delete", payload_c)
        self.assertIn("editors", payload_c)
        self.assertIn("nodedefs", payload_c)

        editors_by_id = {e["id"]: e for e in payload_c["editors"]}
        for ed_id in editors_by_id:
            self.assertRegex(ed_id, UPPER_ALNUM_RE)

        # Verify TTIMESTAMP uses uom=151 (Unix timestamp)
        self.assertIn("TTIMESTAMP", editors_by_id)
        ts_ranges = editors_by_id["TTIMESTAMP"]["ranges"]
        self.assertEqual(ts_ranges[0]["uom"], "151")

        # Verify TEMPERATURE editor range ordering switches for C vs F
        self.assertEqual(editors_by_id["TEMPERATURE"]["ranges"][0]["uom"], "4")
        payload_f = lib._dynamic_profile_payload("F")
        editors_f = {e["id"]: e for e in payload_f["editors"]}
        self.assertEqual(editors_f["TEMPERATURE"]["ranges"][0]["uom"], "17")

        # Verify all nodedef properties have names and valid editors
        nodedefs_by_id = {n["id"]: n for n in payload_c["nodedefs"]}
        self.assertEqual(set(nodedefs_by_id.keys()), {"CONTROLLER", "ROOM", "VALVE"})
        for nd_id, nd in nodedefs_by_id.items():
            for prop in nd["properties"]:
                self.assertRegex(prop["id"], UPPER_ALNUM_RE)
                self.assertIn(prop["editor"], editors_by_id)
                self.assertTrue(prop.get("name"), f"Missing name for {nd_id}.{prop['id']}")

    def test_driver_names_loaded_from_profile_and_dynamic_fallback(self):
        for nd_id, expected_st in (
            ("CONTROLLER", "NodeServer State"),
            ("ROOM", "Room State"),
            ("VALVE", "Valve State"),
        ):
            static_names = lib.get_driver_names_from_profile(nd_id)
            dynamic_names = lib._load_driver_names_from_dynamic_profile(nd_id)
            self.assertEqual(static_names, dynamic_names)
            self.assertEqual(static_names.get("ST"), expected_st)
        self.assertEqual(lib.get_driver_names_from_profile("ROOM").get("GV3"), "Last Update Time")


if __name__ == "__main__":
    unittest.main()

