"""Unit tests for NetatmoCloud OAuth and Energy API methods."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from tests.mock_udi import MockPolyglot, install_mock_udi_interface

install_mock_udi_interface()
from NetatmoOauthEnergy import NetatmoCloud  # noqa: E402


SAMPLE_HOMESDATA = {
    "status": "ok",
    "body": {
        "homes": [
            {
                "id": "home_energy_1",
                "name": "Main House",
                "modules": [
                    {"id": "70:ee:50:00:01:01", "type": "NAPlug", "name": "Relay"},
                    {"id": "09:00:00:00:02:02", "type": "NRV", "name": "Living Valve", "room_id": "1112223334"},
                ],
                "rooms": [
                    {"id": "1112223334", "name": "Living Room", "module_ids": ["09:00:00:00:02:02"]},
                ],
            },
            {
                "id": "home_weather_2",
                "name": "Cabin Weather Only",
                "modules": [
                    {"id": "70:ee:50:99:99:99", "type": "NAMain", "name": "Weather"},
                ],
                "rooms": [],
            },
        ]
    },
}

SAMPLE_HOMESTATUS = {
    "status": "ok",
    "time_server": 1730000123,
    "body": {
        "home": {
            "id": "home_energy_1",
            "modules": [
                {
                    "id": "09:00:00:00:02:02",
                    "type": "NRV",
                    "reachable": True,
                    "battery_state": "high",
                    "battery_level": 3100,
                    "rf_strength": 64,
                }
            ],
            "rooms": [
                {
                    "id": "1112223334",
                    "reachable": True,
                    "therm_measured_temperature": 20.5,
                    "therm_setpoint_temperature": 21.0,
                    "therm_setpoint_mode": "schedule",
                    "heating_power_request": 45,
                    "open_window": False,
                    "anticipating": True,
                }
            ],
        }
    },
}


class TestNetatmoCloudApi(unittest.TestCase):
    def setUp(self):
        self.poly = MockPolyglot()
        with patch("time.sleep"):
            self.cloud = NetatmoCloud(self.poly, "read_thermostat write_thermostat")

    def test_custom_params_handler_accepts_both_case_conventions(self):
        self.cloud.customParamsHandler({
            "ClientID": "my_client_id",
            "ClientSecret": "my_client_secret",
            "TEMP_UNIT": "Fahrenheit",
        })
        self.assertTrue(self.cloud.customParamsDone())
        self.assertEqual(self.cloud.client_ID, "my_client_id")
        self.assertEqual(self.cloud.client_SECRET, "my_client_secret")
        self.assertEqual(self.cloud.temp_unit, "F")
        self.assertNotIn("client", self.poly.Notices)

    def test_custom_params_handler_sets_notice_when_missing(self):
        self.cloud.customParamsHandler({})
        self.assertFalse(self.cloud.customParamsDone())
        self.assertIn("client", self.poly.Notices)
        self.assertEqual(self.cloud.customParameters["TEMP_UNIT"], "C")

    def test_get_energy_homes_filters_only_energy_homes(self):
        with patch.object(self.cloud, "_callApi", return_value=SAMPLE_HOMESDATA):
            homes = self.cloud.get_energy_homes()
        self.assertIn("home_energy_1", homes)
        self.assertNotIn("home_weather_2", homes)

    def test_get_home_status_and_getters_with_uom151_timestamp(self):
        with patch.object(self.cloud, "_callApi", return_value=SAMPLE_HOMESTATUS):
            status = self.cloud.get_home_status("home_energy_1")
        self.assertIsNotNone(status)
        self.assertEqual(self.cloud.get_last_update_time("home_energy_1"), 1730000123)
        self.assertEqual(self.cloud.get_room_temp("home_energy_1", "1112223334"), 20.5)
        self.assertEqual(self.cloud.get_room_setpoint_temp("home_energy_1", "1112223334"), 21.0)
        self.assertEqual(self.cloud.get_room_setpoint_mode("home_energy_1", "1112223334"), "schedule")
        self.assertEqual(self.cloud.get_room_heat_power_request("home_energy_1", "1112223334"), 45)
        self.assertFalse(self.cloud.get_room_open_window("home_energy_1", "1112223334"))
        self.assertTrue(self.cloud.get_room_anticipating("home_energy_1", "1112223334"))
        self.assertTrue(self.cloud.get_valve_online("home_energy_1", "09:00:00:00:02:02"))
        self.assertEqual(self.cloud.get_valve_bat_state("home_energy_1", "09:00:00:00:02:02"), "high")
        self.assertEqual(self.cloud.get_valve_bat_level("home_energy_1", "09:00:00:00:02:02"), 3100)
        self.assertEqual(self.cloud.get_valve_rf_strength("home_energy_1", "09:00:00:00:02:02"), 64)

    def test_execute_set_setpoint_and_mode_endpoints(self):
        calls = []

        def fake_call_api(method, url, body=None):
            calls.append((method, url, body))
            return {"status": "ok"}

        with patch.object(self.cloud, "_callApi", side_effect=fake_call_api):
            self.cloud.execute_set_setpoint("home_1", "room_1", 21.5, "manual", 1730003600)
            self.cloud.execute_set_setpoint("home_1", "room_1", None, "home", 0)
            self.cloud.execute_set_mode("home_1", "away", 1730007200)

        self.assertEqual(
            calls[0],
            ("POST", "/setroomthermpoint?home_id=home_1&room_id=room_1&mode=manual&temp=21.5&endtime=1730003600", None),
        )
        self.assertEqual(
            calls[1],
            ("POST", "/setroomthermpoint?home_id=home_1&room_id=room_1&mode=home", None),
        )
        self.assertEqual(
            calls[2],
            ("POST", "/setthermmode?home_id=home_1&mode=away&endtime=1730007200", None),
        )


if __name__ == "__main__":
    unittest.main()

