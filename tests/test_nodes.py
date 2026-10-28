"""Unit tests for NetatmoController, udiNetatmoEnergyRoom, and udiNetatmoEnergyValve."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from tests.mock_udi import MockPolyglot, install_mock_udi_interface
from tests.test_api_oauth import SAMPLE_HOMESDATA, SAMPLE_HOMESTATUS

install_mock_udi_interface()
from udiNetatmoEnergy import NetatmoController  # noqa: E402
from udiNetatmoEnergyRoom import udiNetatmoEnergyRoom  # noqa: E402
from udiNetatmoEnergyValve import udiNetatmoEnergyValve  # noqa: E402


class TestNodesAndLifecycle(unittest.TestCase):
    def setUp(self):
        self.stale_db_nodes = [
            {"address": "controller", "primaryNode": "controller", "name": "Netatmo Energy"},
            {"address": "room9999999999", "primaryNode": "room9999999999", "name": "Old Room"},
            {"address": "090000009999", "primaryNode": "room1112223334", "name": "Orphan Valve"},
        ]
        self.poly = MockPolyglot(db_nodes=self.stale_db_nodes)

    def _FakeApi(self, method, url, body=None):
        if url.startswith("/homesdata"):
            return SAMPLE_HOMESDATA
        if url.startswith("/homestatus"):
            return SAMPLE_HOMESTATUS
        return {"status": "ok"}

    def test_dynamic_profile_loaded_only_after_configdone(self):
        with patch("time.sleep"):
            ctrl = NetatmoController(self.poly, "controller", "controller", "Netatmo Energy")

        # Profile must not be loaded before PG3x finishes initialization (CONFIGDONE)
        self.assertEqual(len(self.poly.json_profiles), 0)
        self.assertEqual(ctrl.id, "CONTROLLER")
        self.assertEqual(ctrl.drivers[0]["name"], "NodeServer State")

        # Trigger CONFIGDONE and verify dynamic JSON profile is published
        ctrl.configDoneHandler()
        self.assertTrue(ctrl.configDone)
        self.assertEqual(len(self.poly.json_profiles), 1)
        published_payload, options = self.poly.json_profiles[0]
        self.assertEqual(options, {"waitResponse": True})
        self.assertEqual(
            [nd["id"] for nd in published_payload["nodedefs"]],
            ["CONTROLLER", "ROOM", "VALVE"],
        )

    def test_full_startup_node_discovery_driver_updates_and_db_cleanup(self):
        with patch("time.sleep"):
            ctrl = NetatmoController(self.poly, "controller", "controller", "Netatmo Energy")
            ctrl.myNetatmo.customParamsHandler({
                "clientID": "id123",
                "clientSecret": "sec123",
                "TEMP_UNIT": "C",
                "Main House": "1",  # string '1' as saved by PG3x UI
            })
            ctrl.myNetatmo.customNsHandler("nsdata", {})
            ctrl.configDoneHandler()

            with patch.object(ctrl.myNetatmo, "_callApi", side_effect=self._FakeApi):
                ctrl.start()

                room_node = self.poly.getNode("room1112223334")
                self.assertIsNotNone(room_node)
                self.assertIsInstance(room_node, udiNetatmoEnergyRoom)
                self.assertEqual(room_node.id, "ROOM")

                # Run room.start() to add child valve and update drivers
                room_node.start()
                valve_node = self.poly.getNode("090000000202")
                self.assertIsNotNone(valve_node)
                self.assertIsInstance(valve_node, udiNetatmoEnergyValve)
                self.assertEqual(valve_node.id, "VALVE")
                valve_node.start()

        # Verify stale room and orphaned valve were both deleted
        self.assertIn("room9999999999", self.poly.deleted_nodes)
        self.assertIn("090000009999", self.poly.deleted_nodes)
        self.assertNotIn("controller", self.poly.deleted_nodes)

        # Verify Room drivers (Celsius + uom=151 timestamp)
        self.assertEqual(room_node.driver_values["ST"]["value"], 1)
        self.assertEqual(room_node.driver_values["CLITEMP"]["value"], 20.5)
        self.assertEqual(room_node.driver_values["CLITEMP"]["uom"], 4)
        self.assertEqual(room_node.driver_values["CLISPH"]["value"], 21.0)
        self.assertEqual(room_node.driver_values["CLIMD"]["value"], 0)
        self.assertEqual(room_node.driver_values["GV0"]["value"], 45)
        self.assertEqual(room_node.driver_values["GV1"]["value"], 0)
        self.assertEqual(room_node.driver_values["GV2"]["value"], 1)
        self.assertEqual(room_node.driver_values["GV3"]["value"], 1730000123)
        self.assertEqual(room_node.driver_values["GV3"]["uom"], 151)

        # Verify Valve drivers
        self.assertEqual(valve_node.driver_values["ST"]["value"], 1)
        self.assertEqual(valve_node.driver_values["GV0"]["value"], 2)  # 'high' -> 2
        self.assertEqual(valve_node.driver_values["GV1"]["value"], -64)
        self.assertEqual(valve_node.driver_values["GV1"]["uom"], 131)
        self.assertEqual(valve_node.driver_values["GV2"]["value"], 3.1)
        self.assertEqual(valve_node.driver_values["GV2"]["uom"], 72)

    def test_room_commands_setpoint_and_opmode_and_stop_offline(self):
        with patch("time.sleep"):
            ctrl = NetatmoController(self.poly, "controller", "controller", "Netatmo Energy")
            ctrl.myNetatmo.customParamsHandler({
                "clientID": "id123",
                "clientSecret": "sec123",
                "TEMP_UNIT": "F",
            })
            ctrl.myNetatmo.customNsHandler("nsdata", {})
            ctrl.configDoneHandler()

            with patch.object(ctrl.myNetatmo, "_callApi", side_effect=self._FakeApi):
                ctrl.start()
                room_node = self.poly.getNode("room1112223334")
                room_node.start()
                valve_node = self.poly.getNode("090000000202")
                valve_node.start()

                with patch.object(ctrl.myNetatmo, "execute_set_setpoint", return_value={"status": "ok"}) as mock_sp:
                    room_node.set_setpoint({
                        "address": "room1112223334",
                        "cmd": "SETPOINT",
                        "query": {"STEMP.uom17": "68.0", "SPMODE.uom25": "1", "ACTIVET.uom44": "0"},
                    })
                    mock_sp.assert_called_once_with("home_energy_1", "1112223334", 20.0, "home", 0)

                with patch.object(ctrl.myNetatmo, "execute_set_mode", return_value={"status": "ok"}) as mock_mode:
                    room_node.set_opmode({
                        "address": "room1112223334",
                        "cmd": "OPMODE",
                        "query": {"OPMODE.uom25": "2", "ACTIVET.uom44": "0"},
                    })
                    mock_mode.assert_called_once_with("home_energy_1", "hg", 0)

        # Verify stopHandler marks all nodes offline
        ctrl.stopHandler()
        self.assertTrue(self.poly.stopped)
        self.assertEqual(ctrl.driver_values["ST"]["value"], 0)
        self.assertEqual(room_node.driver_values["ST"]["value"], 0)
        self.assertEqual(valve_node.driver_values["ST"]["value"], 0)

    def test_system_poll_guard_and_offline_drivers(self):
        with patch("time.sleep"):
            ctrl = NetatmoController(self.poly, "controller", "controller", "Netatmo Energy")
            # Poll before nodeDefineDone should be a no-op
            with patch.object(ctrl.myNetatmo, "get_home_status") as mock_status:
                ctrl.systemPoll("shortPoll")
                mock_status.assert_not_called()

            ctrl.myNetatmo.customParamsHandler({
                "clientID": "id123",
                "clientSecret": "sec123",
                "TEMP_UNIT": "C",
            })
            ctrl.myNetatmo.customNsHandler("nsdata", {})
            ctrl.configDoneHandler()

            with patch.object(ctrl.myNetatmo, "_callApi", side_effect=self._FakeApi):
                ctrl.start()
                room_node = self.poly.getNode("room1112223334")
                room_node.start()
                valve_node = self.poly.getNode("090000000202")
                valve_node.start()

                # Test shortPoll and longPoll only poll enabled energy homes
                with patch.object(ctrl.myNetatmo, "get_home_status", wraps=ctrl.myNetatmo.get_home_status) as spy_status:
                    ctrl.systemPoll("shortPoll")
                    spy_status.assert_called_once_with("home_energy_1")
                    self.assertEqual(ctrl.reported_cmds[-1], ("DON", 2))

            # Mark room and valve unreachable and verify offline driver fallback (99 / uom=25)
            ctrl.myNetatmo.energy_data["home_energy_1"]["rooms"]["1112223334"]["reachable"] = False
            ctrl.myNetatmo.energy_data["home_energy_1"]["modules"]["09:00:00:00:02:02"]["reachable"] = False
            room_node.updateISYdrivers()
            valve_node.updateISYdrivers()

            self.assertEqual(room_node.driver_values["ST"]["value"], 0)
            self.assertEqual(room_node.driver_values["CLITEMP"]["value"], 99)
            self.assertEqual(room_node.driver_values["GV3"]["value"], 99)
            self.assertEqual(valve_node.driver_values["ST"]["value"], 0)
            self.assertEqual(valve_node.driver_values["GV0"]["value"], 99)
            self.assertEqual(valve_node.driver_values["GV1"]["value"], 99)
            self.assertEqual(valve_node.driver_values["GV2"]["value"], 99)


if __name__ == "__main__":
    unittest.main()
