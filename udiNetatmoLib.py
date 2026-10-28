
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)

from os import truncate
from pathlib import Path
import xml.etree.ElementTree as ET
#import udi_interface
#import sys
import time
import math


def _profile_editors(temp_unit: str = "C") -> list:
    is_fahrenheit = str(temp_unit or "C").strip().upper().startswith("F")
    temp_ranges = (
        [
            {"uom": "17", "min": -50, "max": 150, "prec": 1},
            {"uom": "4", "min": -50, "max": 65, "prec": 1},
            {"uom": "25", "subset": "0,99", "names": {"0": "No support", "99": "Unknown"}},
        ]
        if is_fahrenheit
        else [
            {"uom": "4", "min": -50, "max": 65, "prec": 1},
            {"uom": "17", "min": -50, "max": 150, "prec": 1},
            {"uom": "25", "subset": "0,99", "names": {"0": "No support", "99": "Unknown"}},
        ]
    )
    set_temp_ranges = (
        [
            {"uom": "17", "min": 41, "max": 95, "step": 0.5, "prec": 1},
            {"uom": "4", "min": 5, "max": 35, "step": 0.5, "prec": 1},
        ]
        if is_fahrenheit
        else [
            {"uom": "4", "min": 5, "max": 35, "step": 0.5, "prec": 1},
            {"uom": "17", "min": 41, "max": 95, "step": 0.5, "prec": 1},
        ]
    )
    return [
        {
            "id": "STATUS",
            "ranges": [{"uom": "25", "subset": "0,1"}],
        },
        {
            "id": "BOOL",
            "ranges": [
                {"uom": "2", "subset": "0,1"},
                {"uom": "25", "subset": "99", "names": {"99": "Unknown"}},
            ],
        },
        {
            "id": "CONNECT",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0-1,99",
                    "names": {"0": "Not Connected", "1": "Connected", "99": "Unknown"},
                }
            ],
        },
        {
            "id": "TEMPERATURE",
            "ranges": temp_ranges,
        },
        {
            "id": "SETTEMP",
            "ranges": set_temp_ranges,
        },
        {
            "id": "TTIMESTAMP",
            "ranges": [
                {"uom": "44", "min": 0, "max": 525600, "prec": 1},
                {"uom": "25", "subset": "99", "names": {"99": "Unknown"}},
            ],
        },
        {
            "id": "TCTRLMODE",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0-3,99",
                    "names": {
                        "0": "Schedule",
                        "1": "Away",
                        "2": "Frost Guard",
                        "3": "Manual",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "SETCLIMD",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0-2",
                    "names": {
                        "0": "Schedule",
                        "1": "Away",
                        "2": "Frost Guard",
                    },
                }
            ],
        },
        {
            "id": "ENERGYREQ",
            "ranges": [
                {"uom": "0", "min": 0, "max": 10000},
                {"uom": "25", "subset": "0,99", "names": {"0": "No support", "99": "Unknown"}},
            ],
        },
        {
            "id": "THMODE",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0-1",
                    "names": {"0": "Manual", "1": "Home/Schedule"},
                }
            ],
        },
        {
            "id": "TMIN",
            "ranges": [{"uom": "44", "min": 0, "max": 120, "prec": 0}],
        },
        {
            "id": "BATTERY",
            "ranges": [
                {
                    "uom": "25",
                    "subset": "0-5,99",
                    "names": {
                        "0": "Maximum",
                        "1": "Full",
                        "2": "High",
                        "3": "Medium",
                        "4": "Low",
                        "5": "Very Low",
                        "99": "Unknown",
                    },
                }
            ],
        },
        {
            "id": "BATVALUE",
            "ranges": [
                {"uom": "72", "min": 0, "max": 7, "prec": 2},
                {"uom": "25", "subset": "0,99", "names": {"0": "No support", "99": "Unknown"}},
            ],
        },
        {
            "id": "RFSTRENGTH",
            "ranges": [
                {"uom": "131", "min": -100, "max": 174},
                {"uom": "25", "subset": "0,99", "names": {"0": "No support", "99": "Unknown"}},
            ],
        },
    ]


def _dynamic_profile_payload(temp_unit: str = "C") -> dict:
    return {
        "delete": {
            "editors": ["*"],
            "nodedefs": ["*"],
            "linkdefs": ["*"],
        },
        "editors": _profile_editors(temp_unit),
        "nodedefs": [
            {
                "id": "CONTROLLER",
                "name": "Netatmo Energy System",
                "icon": "EnergyMonitor",
                "properties": [
                    {"id": "ST", "editor": "CONNECT", "name": "NodeServer State"},
                ],
                "cmds": {
                    "sends": [
                        {"id": "DON"},
                        {"id": "DOF"},
                    ],
                    "accepts": [
                        {"id": "UPDATE", "name": "Force Update"},
                    ],
                },
                "links": {"ctl": [], "rsp": []},
            },
            {
                "id": "ROOM",
                "name": "Room",
                "icon": "Thermostat",
                "properties": [
                    {"id": "ST", "editor": "CONNECT", "name": "Room State"},
                    {"id": "CLITEMP", "editor": "TEMPERATURE", "name": "Temperature"},
                    {"id": "CLISPH", "editor": "TEMPERATURE", "name": "Set Point"},
                    {"id": "CLIMD", "editor": "TCTRLMODE", "name": "Mode"},
                    {"id": "GV0", "editor": "ENERGYREQ", "name": "Energy Request"},
                    {"id": "GV1", "editor": "BOOL", "name": "Window Open"},
                    {"id": "GV2", "editor": "BOOL", "name": "Predictive"},
                    {"id": "GV3", "editor": "TTIMESTAMP", "name": "Time Since Update"},
                ],
                "cmds": {
                    "sends": [],
                    "accepts": [
                        {"id": "UPDATE", "name": "Force Update"},
                        {
                            "id": "SETPOINT",
                            "name": "Set Setpoint",
                            "parameters": [
                                {"id": "STEMP", "name": "Setpoint temp", "editor": "SETTEMP", "init": "CLISPH"},
                                {"id": "SPMODE", "name": "Setpoint mode", "editor": "THMODE", "init": "0"},
                                {"id": "ACTIVET", "name": "Active time", "editor": "TMIN", "init": "0"},
                            ],
                        },
                        {
                            "id": "OPMODE",
                            "name": "Set Mode",
                            "parameters": [
                                {"id": "OPMODE", "name": "Operation mode", "editor": "SETCLIMD", "init": "CLIMD"},
                                {"id": "ACTIVET", "name": "Active time", "editor": "TMIN", "init": "0"},
                            ],
                        },
                    ],
                },
                "links": {"ctl": [], "rsp": []},
            },
            {
                "id": "VALVE",
                "name": "Valve",
                "icon": "Thermostat",
                "properties": [
                    {"id": "ST", "editor": "CONNECT", "name": "Valve State"},
                    {"id": "GV0", "editor": "BATTERY", "name": "Battery Level"},
                    {"id": "GV1", "editor": "RFSTRENGTH", "name": "RF Strength"},
                    {"id": "GV2", "editor": "BATVALUE", "name": "Battery Reading"},
                ],
                "cmds": {
                    "sends": [],
                    "accepts": [
                        {"id": "UPDATE", "name": "Force Update"},
                    ],
                },
                "links": {"ctl": [], "rsp": []},
            },
        ],
        "linkdefs": [],
    }


def _load_driver_names_from_profile_dir(profile_dir: Path, nodedef_id: str) -> dict:
    """Parse driver names from a static profile directory (nodedef + NLS files) if present."""
    names = {}
    target_id = str(nodedef_id or "").strip().upper()
    if not target_id or not profile_dir.is_dir():
        return names

    nls_prefix = None
    nodedef_dir = profile_dir / "nodedef"
    if nodedef_dir.is_dir():
        for xml_file in nodedef_dir.glob("*.xml"):
            try:
                root = ET.parse(xml_file).getroot()
                for nd in root.findall(".//nodeDef"):
                    nd_id = (nd.attrib.get("id") or "").strip().upper()
                    if nd_id == target_id:
                        nls_prefix = (nd.attrib.get("nls") or "").strip().upper()
                        break
            except Exception as err:
                logging.debug("Failed to read nodedef file {}: {}".format(xml_file, err))

    nls_dir = profile_dir / "nls"
    if nls_dir.is_dir():
        for nls_file in nls_dir.glob("*.txt"):
            try:
                for line in nls_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = [part.strip() for part in line.split("=", 1)]
                    parts = [p.strip().upper() for p in key.split("-")]
                    if len(parts) >= 4 and parts[0] == "ST" and parts[-1] == "NAME":
                        if nls_prefix and parts[1] == nls_prefix:
                            names[parts[2]] = val
                        elif parts[1] == target_id:
                            names.setdefault(parts[2], val)
                    elif len(parts) >= 4 and parts[0] == "ND" and parts[1] == target_id and parts[-1] == "NAME":
                        names[parts[2]] = val
            except Exception as err:
                logging.debug("Failed to read NLS file {}: {}".format(nls_file, err))
    return names


def _load_driver_names_from_dynamic_profile(nodedef_id: str, temp_unit: str = "C") -> dict:
    """Extract driver human-readable names from the dynamic profile generated in code."""
    target_id = str(nodedef_id or "").strip().upper()
    payload = _dynamic_profile_payload(temp_unit)
    for nd in payload.get("nodedefs", []):
        if str(nd.get("id", "")).strip().upper() == target_id:
            return {
                prop["id"]: prop.get("name", prop["id"])
                for prop in nd.get("properties", [])
                if "id" in prop
            }
    return {}


def get_driver_names_from_profile(nodedef_id: str, temp_unit: str = "C") -> dict:
    """Retrieve driver names from the profile directory or dynamic profile generated in code."""
    profile_dir = Path(__file__).resolve().parent / "profile"
    if profile_dir.is_dir():
        names = _load_driver_names_from_profile_dir(profile_dir, nodedef_id)
        if names:
            return names
    return _load_driver_names_from_dynamic_profile(nodedef_id, temp_unit)


def apply_profile_driver_names(self, nodedef_id: str = None) -> None:
    """Synchronize driver['name'] fields on self.drivers from profile definitions."""
    target_id = (nodedef_id or getattr(self, "id", "") or "").strip()
    drivers = getattr(self, "drivers", None)
    if not target_id or not isinstance(drivers, list):
        return
    profile_names = get_driver_names_from_profile(target_id)
    for drv in drivers:
        if isinstance(drv, dict) and drv.get("driver"):
            label = profile_names.get(drv["driver"])
            if label:
                drv["name"] = label


def update_dynamic_profile(self, temp_unit: str = "C", force: bool = False) -> bool:
    """Publish dynamic JSON profile via updateJsonProfile after PG3x initialization."""
    if not getattr(self, "configDone", False):
        logging.info("Deferring dynamic profile load until PG3x completes initialization (CONFIGDONE)")
        return False

    payload = _dynamic_profile_payload(temp_unit)
    last_payload = getattr(self, "_last_published_profile", None)
    if not force and last_payload == payload:
        logging.debug("Dynamic profile already up to date; skipping")
        return True

    updater = getattr(self.poly, "updateJsonProfile", None)
    if callable(updater):
        try:
            updater(payload, {"waitResponse": True})
            self._last_published_profile = payload
            logging.info("Dynamic JSON profile updated successfully")
            return True
        except TypeError:
            try:
                updater(payload)
                self._last_published_profile = payload
                logging.info("Dynamic JSON profile updated successfully")
                return True
            except Exception as err:
                logging.error("Dynamic profile update failed: {}".format(err))
        except Exception as err:
            logging.error("Dynamic profile update failed: {}".format(err))
    else:
        logging.warning("updateJsonProfile not available; falling back to static updateProfile()")
        self.poly.updateProfile()
        self._last_published_profile = payload
    return False

def node_queue(self, data):
    if isinstance(data, dict) and data.get('address') == getattr(self, 'address', None):
        self.n_queue.append(data['address'])

def wait_for_node_done(self):
    while len(self.n_queue) == 0:
        time.sleep(0.1)
    self.n_queue.pop()

def prepare_node_adr(self, dev_adr, length):
    dev_adr = str(dev_adr)
    dev_adr = dev_adr.replace(':','')
    dev_adr = dev_adr[-length:]
    return(dev_adr)


def heartbeat(self):
    logging.debug('heartbeat: ' + str(self.hb))
    self.node.setDriver('ST', 1)
    if self.hb == 0:
        self.reportCmd('DON',2)
        self.hb = 1
    else:
        self.reportCmd('DOF',2)
        self.hb = 0

def update_ISY_data(self):
    logging.info('update_ISY_data executing:')
    nodes = self.poly.nodes()
    for nde in nodes:
        if nde.address != 'controller':   # but not the setup node
            logging.debug('updating node {} data'.format(nde))
            nde.updateISYdrivers()
            
def ISY2op_mode (self, mode_nbr):
    if mode_nbr == 0:
        mode_str = 'schedule'
    elif mode_nbr == 1:
        mode_str = 'away'
    elif mode_nbr == 2:
        mode_str = 'hg'
    else:
        mode_str = 'unknown'+str(mode_nbr)
    return(mode_str)

def ISY2sp_mode (self, mode_nbr):
    if mode_nbr == 0:
        mode_str = 'manual'
    elif mode_nbr == 2:
        mode_str = 'max'
    elif mode_nbr == 1:
        mode_str = 'home'
    else:
        mode_str = 'unknown'+str(mode_nbr)
    return(mode_str)



def rfstate2ISY(self, rf_state):
    if rf_state.lower() == 'full':
        rf = 0
    elif rf_state.lower() == 'medium':
        rf = 1
    elif rf_state.lower() == 'low':
        rf = 2
    else:
        rf= 99
        logging.error('Unsupported RF state {}'.format(rf_state))
    return(rf)

def t_mode2ISY(self, mode):
    if mode in ('schedule', 'home'):
        mod = 0
    elif mode =='away':
        mod = 1
    elif mode == 'hg':
        mod = 2
    elif mode == 'manual':
        mod = 3
    else:
        mod = 99
    return(mod)

def battery2ISY(self, batlvl):
    if batlvl == 'max':
        state = 0
    elif batlvl == 'full':
        state = 1
    elif batlvl == 'high':
        state = 2
    elif batlvl == 'medium':
        state = 3
    elif batlvl == 'low':
        state = 4
    elif batlvl == 'very low':
        state = 5
    else:
        state = 99
    return(state)

def trend2ISY (self, trend):
    if trend == 'stable':
        return(0)
    elif trend == 'up':
        return(1)
    elif trend =='down':
        return(2)
    else:
        logging.error('unsupported temperature trend: {}'.format(trend))
        return(99)    

def con_state2ISY(self, state):
    if state == None:
        con = 99
    elif state == False:
        con = 0
    else:
        con = 1
    return(con)

def convert_temp_unit(self, tempStr):
    if str(tempStr).capitalize()[:1] == 'F':
        return(1)
    elif str(tempStr).capitalize()[:1] == 'C':
        return(0)
    return(0)


def bool2ISY (self, data):
    if data:
        return(1)
    else:
        return(0)

def state2Nbr(self, val):
    if val == 'normal':
        return(0)
    elif val == 'alert':
        return(1)
    else:
        return(99)

def isy_value(self, value):
    if value == None:
        return (99)
    else:
        return(value)
