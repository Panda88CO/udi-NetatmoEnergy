# Netatmo Energy Node Server (`udi-NetatmoEnergy`)

Polyglot v3x (PG3x) node server for Netatmo Smart Heating / Energy devices (Smart Radiator Valves, Smart Thermostats, and OpenTherm/Smarther Thermostats).

## Features
- **Controller Node (`CONTROLLER`)**:
  - Reports NodeServer connection state (`ST`) and sends a `DON`/`DOF` heartbeat on each `shortPoll`.
  - Dynamically loads the JSON profile after PG3x completes initialization (`CONFIGDONE`).
- **Room Node (`ROOM`)**:
  - Created for each room in enabled Netatmo homes that contains a Netatmo radiator valve (`NRV`) or thermostat (`NATherm1`, `OTM`, `BNS`).
  - Reports Room State (`ST`), Measured Temperature (`CLITEMP`), Set Point (`CLISPH`), Mode (`CLIMD`: Schedule, Away, Frost Guard, Manual), Energy Request (`GV0`), Window Open (`GV1`), Predictive Heating (`GV2`), and Last Update Time (`GV3`, Unix timestamp `uom=151`).
  - Supports **Set Setpoint** (`SETPOINT`: target temperature, Manual or Home/Schedule mode, and optional active duration in minutes) and **Set Mode** (`OPMODE`: Schedule, Away, or Frost Guard mode with optional active duration in minutes).
- **Valve / Thermostat Subnode (`VALVE`)**:
  - Created under each Room node for each radiator valve or wireless thermostat in that room.
  - Reports Valve State (`ST`), Battery Level (`GV0`: Maximum, Full, High, Medium, Low, Very Low), RF Signal Strength (`GV1` in dBm), and Battery Reading (`GV2` in Volts).

## System Requirements
- **PG3x** 3.3.0 or greater (PG3 is not supported because OAuth2 requires PG3x)
- **`udi_interface`** 3.3.5 or greater

---

## Quick Start Guide for New Users

### 1. Create Your Netatmo Developer Credentials
To allow the node server to communicate with your Netatmo account, you need a personal Netatmo Developer App:
1. Log in to the Netatmo Developer Portal at [https://dev.netatmo.com](https://dev.netatmo.com) using your normal Netatmo account.
2. Go to **My Apps** and click **Create**.
3. Enter an **App Name** and **Description**, accept the terms, and click **Save**.
4. Copy the **Client ID** and **Client Secret** shown on your app page.
   > **Important:** If you use other Netatmo node servers (such as Netatmo Weather), create a separate Developer App with its own Client ID and Client Secret for Netatmo Energy.

### 2. Configure the Node Server in PG3x
1. Install and start the **Netatmo Energy** node server from the PG3x Node Server Store.
2. Open the node server's **Configuration** tab in PG3x and set the following Custom Configuration Parameters:
   - `clientID`: Paste your Netatmo App **Client ID**.
   - `clientSecret`: Paste your Netatmo App **Client Secret**.
   - `TEMP_UNIT`: Set to `C` (default) for Celsius or `F` for Fahrenheit. (Note: Netatmo hardware natively displays Celsius on the physical valves, while IoX will display and accept setpoints in your chosen `TEMP_UNIT`.)
3. Click **Save Changes** and **Restart** the node server.

### 3. Complete OAuth2 Authentication
1. After restarting, you will see a notice in PG3x: **Please initiate authentication**.
2. Click the **Authenticate** button in the PG3x UI.
3. A browser window will open to Netatmo's login page. Sign in and click **Accept** to authorize access.
4. Once redirected back to PG3x, the node server will automatically discover your Netatmo Energy homes, rooms, and valves.

### 4. Selecting Homes (Optional)
- After initial discovery, each Netatmo home with Energy devices is added as a custom parameter in PG3x Configuration with a default value of `1` (Enabled).
- To exclude a home, change its parameter value to `0`, click **Save Changes**, and **Restart** the node server.

---

## Polling Configuration
- **Short Poll (`shortPoll`)**: Default is **300 seconds (5 minutes)**. Polls current room temperatures, setpoints, modes, and valve status (`/homestatus`) and toggles the controller heartbeat (`DON`/`DOF`).
- **Long Poll (`longPoll`)**: Default is **3600 seconds (60 minutes)**. Refreshes home layout (`/homesdata`) and updates all room and valve drivers.

## Release Notes
- **0.2.0**
  - Added dynamic JSON profile loading (`updateJsonProfile`) after PG3x `CONFIGDONE` initialization.
  - Updated all node definitions, editors, and NLS identifiers to uppercase alphanumeric and added human-readable driver names.
  - Updated Room `GV3` (`TTIMESTAMP`) to report Last Update Time as a Unix timestamp (`uom=151`).
  - Added support for Netatmo thermostat/gateway types (`NATherm1`, `OTH`, `OTM`, `BNS`) alongside `NRV` valves.
  - Improved API error handling, stale/orphaned node cleanup, and added unit test suite (`run_tests.py`).
- **0.1.8**
  - Initial PG3x OAuth2 release.

## License
MIT License

