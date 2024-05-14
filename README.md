
# Netatmo Energy NodeServer

Netatmo Energy (valves) NodeServer for PG3, PG3x
MIT license.

This node server integrates the Netatmo Smart Vales as part of the energy system. You will need account access to your Netatmo via the Netatmo Developer API https://dev.netatmo.com.  Log in and select My Apps and then Create,  Fill in info and press save - This exposes a client ID and client secret. Note, if you have other NEtatmo systems and node servers, you need to create a new App with separate Client ID and Client Secret keys.
Start the node server under PG3 - go to configuration and enter client ID and client Secret.  Then restart.   First time you do this you should see a text box asking to authendicate.  Press the authendicate button - you should be taken to a new webpage where you login using you Netatmo id and password (used to generate the clientID etc).  Then press accept and you will be returned to the PG3 interface. 
After running a little the differnt main netatmo homes (with energy system) under the account should be listed in configuration.  By default all are active.  If you do not want one system included set the value to 0.
You can send the preferred temp unit, but NEtatmo operates in C.  It will be displayed in the node as the selected unit, but valves will show Celcius
Restart and you should be up and running

If people have the boiler control, I can add this, but I would need access to the system to test it.

Good luck

## Installation

1. Backup Your ISY in case of problems!
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in PG3x - NOTE PG3 is not supported as OAuth library does not work on PG3 
   Got ton configuration and enter clientId and client secret (see above)
   Restart
   Authendicate if asked
   Select weather stations to be used in configuration (1 for enable, 0 for disable)
   Restart node server
   Go to Admin console 

### Node Settings
The settings for this node are:

#### Short Poll
   * Query system instantaneous data. The default is 5 minutes - sends a heart beat as well 0->1 or 1 -> 0
#### Long Poll
   * Query System for all data - mostly update battery state. The default is 60 minutes.

#### ClientID
   * Your Netatmo App Client ID

#### ClientSecret
   * Your Netatmo App Client Secret

#### TEMP_UNIT
   * C (default) of F

## Requirements
   * PG3x ver 3.3.0 or greater
   * UDI_interfae 3.1.1 or greater

# Release Notes

- 0.1.0 02/07/2024
   - Initial version published to github - No support for MAX/Boost - API not working 
