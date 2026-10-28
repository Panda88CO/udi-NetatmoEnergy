# Netatmo Energy Node Server Configuration

## Step 1: Create a Netatmo Developer App
1. Go to [https://dev.netatmo.com](https://dev.netatmo.com) and sign in with your Netatmo account.
2. Navigate to **My Apps** and click **Create** to register a new application.
3. Fill in the required fields (App Name and Description), accept the terms, and click **Save**.
4. Copy the generated **Client ID** and **Client Secret**.
   > **Note:** If you run other Netatmo node servers (e.g., Weather or Home + Control), create a separate Netatmo Developer App with its own `clientID` and `clientSecret` for this node server.

## Step 2: Configure Custom Parameters in PG3x
Enter the following keys under **Configuration -> Custom Configuration Parameters**, then click **Save** and **Restart** the node server:

- `clientID`: Your Netatmo Developer App Client ID (required).
- `clientSecret`: Your Netatmo Developer App Client Secret (required).
- `TEMP_UNIT`: Preferred temperature display unit in IoX/Admin Console (`C` for Celsius by default, or `F` for Fahrenheit).
- `<Home Name>`: Automatically populated after initial discovery for each Netatmo home with Energy devices (`1` = Enabled by default, `0` = Disabled). If you change a home to `0`, restart the node server to remove its nodes.

## Step 3: Authenticate with Netatmo (OAuth2)
1. After entering `clientID` and `clientSecret` and restarting, a **Please initiate authentication** notice will appear at the top of the PG3x UI.
2. Click the **Authenticate** button in PG3x.
3. Sign in with your Netatmo account and click **Accept** to grant access (`read_thermostat` and `write_thermostat`).
4. You will be redirected back to PG3x, and the node server will automatically discover your homes, rooms, and valves/thermostats.

## Polling Parameters
- `shortPoll` (default: 300s / 5 min): Toggles the controller heartbeat (`DON`/`DOF`) and refreshes room/valve status (`/homestatus`) for enabled homes.
- `longPoll` (default: 3600s / 60 min): Refreshes home topology (`/homesdata`) and updates room/valve status.
