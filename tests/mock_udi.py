"""Mock udi_interface harness for unit testing without a live PG3x broker."""

from __future__ import annotations

import logging
import re
import sys
import types


class MockCustom(dict):
    def __init__(self, poly, name):
        super().__init__()
        self.poly = poly
        self.name = name

    def load(self, data):
        if isinstance(data, dict):
            self.update(data)

    def delete(self, key):
        self.pop(key, None)


class MockNode:
    def __init__(self, polyglot, primary, address, name):
        self.poly = polyglot
        self.primary = primary
        self.address = address
        self.name = name
        self.driver_values = {}
        self.reported_cmds = []

    def setDriver(self, driver, value, report=True, force=False, uom=None):
        self.driver_values[driver] = {
            "value": value,
            "report": report,
            "force": force,
            "uom": uom,
        }

    def reportCmd(self, cmd, value=None):
        self.reported_cmds.append((cmd, value))


class MockOAuth:
    def __init__(self, polyglot):
        self.poly = polyglot
        self._oauth_settings = {}
        self._access_token = "mock-access-token"

    def customDataHandler(self, data):
        pass

    def customNsHandler(self, key, data):
        pass

    def oauthHandler(self, token):
        pass

    def updateOauthSettings(self, settings):
        if isinstance(settings, dict):
            self._oauth_settings.update(settings)

    def getOauthSettings(self):
        return dict(self._oauth_settings)

    def getAccessToken(self):
        if self._access_token is None:
            raise ValueError("Access token is not available")
        return self._access_token


class MockPolyglot:
    STOP = "STOP"
    START = "START"
    CUSTOMPARAMS = "CUSTOMPARAMS"
    CUSTOMDATA = "CUSTOMDATA"
    CUSTOMNS = "CUSTOMNS"
    OAUTH = "OAUTH"
    CONFIGDONE = "CONFIGDONE"
    ADDNODEDONE = "ADDNODEDONE"
    POLL = "POLL"

    def __init__(self, db_nodes=None):
        self.Notices = MockCustom(self, "notices")
        self.subscriptions = []
        self._nodes = {}
        self._db_nodes = list(db_nodes or [])
        self.deleted_nodes = []
        self.json_profiles = []
        self.static_profile_updates = 0
        self.ready_called = 0
        self.stopped = False

    def subscribe(self, event, callback, address=None):
        self.subscriptions.append((event, callback, address))

    def addNode(self, node, conn_status=None, rename=False):
        self._nodes[node.address] = node
        # Immediately fire ADDNODEDONE callbacks so wait_for_node_done() unblocks
        payload = {"address": node.address}
        for event, callback, _ in list(self.subscriptions):
            if event == self.ADDNODEDONE:
                callback(payload)
        return node

    def getNode(self, address):
        return self._nodes.get(address)

    def nodes(self):
        return list(self._nodes.values())

    def getNodes(self):
        return dict(self._nodes)

    def getNodesFromDb(self):
        return list(self._db_nodes)

    def delNode(self, address):
        self.deleted_nodes.append(address)
        self._nodes.pop(address, None)

    def getValidName(self, name):
        return re.sub(r"[^A-Za-z0-9_ -]", "", str(name)).strip()

    def getValidAddress(self, address):
        clean = re.sub(r"[^A-Za-z0-9_]", "", str(address)).lower()
        return clean[:14]

    def updateJsonProfile(self, payload, options=None):
        self.json_profiles.append((payload, options))

    def updateProfile(self):
        self.static_profile_updates += 1

    def ready(self):
        self.ready_called += 1

    def stop(self):
        self.stopped = True


def install_mock_udi_interface():
    """Install mock udi_interface (and fallback requests) into sys.modules."""
    logger = logging.getLogger("udi_NetatmoEnergy_test")
    logger.setLevel(logging.CRITICAL)

    mod = types.ModuleType("udi_interface")
    mod.LOGGER = logger
    mod.Custom = MockCustom
    mod.Node = MockNode
    mod.OAuth = MockOAuth
    mod.Interface = MockPolyglot
    sys.modules["udi_interface"] = mod

    try:
        import requests  # noqa: F401
    except ImportError:
        req_mod = types.ModuleType("requests")
        exc_mod = types.ModuleType("requests.exceptions")

        class HTTPError(Exception):
            pass

        class JSONDecodeError(Exception):
            pass

        exc_mod.HTTPError = HTTPError
        exc_mod.JSONDecodeError = JSONDecodeError
        req_mod.exceptions = exc_mod
        req_mod.get = lambda *a, **kw: None
        req_mod.post = lambda *a, **kw: None
        req_mod.patch = lambda *a, **kw: None
        req_mod.delete = lambda *a, **kw: None
        req_mod.put = lambda *a, **kw: None
        sys.modules["requests"] = req_mod
        sys.modules["requests.exceptions"] = exc_mod

    return mod
