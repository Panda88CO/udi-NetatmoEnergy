
#!/usr/bin/env python3

### Your external service class
'''
Your external service class can be named anything you want, and the recommended location would be the lib folder.
It would look like this:

External service sample code
Copyright (C) 2023 Universal Devices

MIT License
'''
import requests
import time
import urllib.parse
from datetime import datetime, timezone
#from udi_interface import LOGGER, Custom
#from oauth import OAuth
try:
    from udi_interface import LOGGER, Custom, OAuth
    logging = LOGGER
    Custom = Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)



# Implements the API calls to your external service
# It inherits the OAuth class
class NetatmoCloud(OAuth):
    yourApiEndpoint = 'https://api.netatmo.com/api'

    def __init__(self, polyglot, scope):
        super().__init__(polyglot)
        logging.info('OAuth initializing')
        self.poly = polyglot
        self.scope = scope
        self.customParameters = Custom(self.poly, 'customparams')
        #self.scope_str = None
        self.apiEndpoint = 'https://api.netatmo.com'
        self.client_ID = None
        self.client_SECRET = None
        self.handleCustomParamsDone = False
        #self.customerDataHandlerDone = False
        self.customNsHandlerDone = False
        self.temp_unit = 'C'

        self.scopeList = ['read_station', 'read_magellan', 'write_magellan', 'read_bubendorff', 'write_bubendorff', 'read_smarther', 'write_smarther', 'read_thermostat','write_thermostat', 'read+_camera', 'write_camera', 'access_camera', 'read_boorbell', 'access_doorbell',
             'read_mx', 'write_mx', 'read_presence', 'write_presence', 'access_presence', 'read_homecoach', 'read_carbonmonoxidedetector', 'read_smokedetector', 'read_mhs1', 'write_mhs1']
        
        self._dev_list  = ['NAPlug', 'NRV', 'NATherm1', 'OTH', 'OTM', 'BNS']

        self.energy_data = {}
        self.GW_modules = ['NAPlug', 'OTH']
        self.valves =['NRV']
        self.thermostat = ['NATherm1', 'OTM', 'BNS']

        #self.customParameters= Custom(polyglot, 'customparams')
        #self.Notices = Custom(self.poly, 'notices')

        logging.info('External service connectivity initialized...')
        #logging.debug('oauth : {}'.format(self.oauthConfig))

        time.sleep(1)
        #while not self.handleCustomParamsDone:
        #    logging.debug('Waiting for customParams to complete - getAccessToken')
        #    time.sleep(0.2)
        # self.getAccessToken()
    
    # The OAuth class needs to be hooked to these 3 handlers
    def customDataHandler(self, data):
        logging.debug('customDataHandler called')
        #while not self.handleCustomParamsDone:
        #    logging.debug('Waiting for customDataHandler to complete')
        #    time.sleep(1)
        super().customDataHandler(data)
        self.customDataHandlerDone = True
        logging.debug('customDataHandler Finished')

    def customNsHandler(self, key, data):
        logging.debug('customNsHandler called')
        #while not self.customParamsDone():
        #    logging.debug('Waiting for customNsHandler to complete')
        #    time.sleep(1)
        #self.updateOauthConfig()
        super().customNsHandler(key, data)
        self.customNsHandlerDone = True
        logging.debug('customNsHandler Finished')

    def oauthHandler(self, token):
        logging.debug('oauthHandler called')
        while not (self.customParamsDone() and self.customNsDone()):
            logging.debug('Waiting for oauthHandler to complete')
            time.sleep(5)
        super().oauthHandler(token)
        self.customOauthHandlerDone = True
        logging.debug('oauthHandler Finished')

    def customNsDone(self):
        return(self.customNsHandlerDone)
    
    def customDateDone(self):
        return(self.customDataHandlerDone )

    def customParamsDone(self):
        return(self.handleCustomParamsDone)
    #def refresh_token(self):
    #    logging.debug('checking token for refresh')
        

    # Your service may need to access custom params as well...
    
    def main_module_enabled(self, node_name):
        logging.debug('main_module_enabled called {}'.format(node_name))
        if node_name in self.customParameters:           
            return(int(self.customParameters[node_name]) == 1)
        else:
            self.customParameters[node_name] = 1 #add and enable by default
            self.poly.Notices['home_id'] = 'Check config to select which home/modules should be used (1 - used, 0 - not used) - then restart'
            return(True)

                
    def customParamsHandler(self, userParams):
        self.customParameters.load(userParams)
        logging.debug('customParamsHandler called {}'.format(userParams))
        client_ok = False
        secret_ok = False
        oauthSettingsUpdate = {}
        # Example for a boolean field

        client_id_val = userParams.get('clientID') or userParams.get('ClientID')
        if client_id_val:
            if client_id_val != 'enter client_id':
                self.client_ID = client_id_val
                oauthSettingsUpdate['client_id'] = client_id_val
                client_ok = True
        else:
            logging.warning('No clientID found')
            self.customParameters['clientID'] = 'enter client_id'
            self.client_ID = None
            
        client_secret_val = self.customParameters['clientSecret'] if 'clientSecret' in self.customParameters else (self.customParameters['ClientSecret'] if 'ClientSecret' in self.customParameters else None)
        if client_secret_val:
            if client_secret_val != 'enter client_secret':
                self.client_SECRET = client_secret_val 
                oauthSettingsUpdate['client_secret'] = client_secret_val
                secret_ok = True
        else:
            logging.warning('No clientSecret found')
            self.customParameters['clientSecret'] = 'enter client_secret'
            self.client_SECRET = None

        if not client_ok  or not secret_ok:
            self.poly.Notices['client'] = 'Please enter valid clientID and clientSecret - then restart'

        if "TEMP_UNIT" in self.customParameters:
            self.temp_unit = self.customParameters['TEMP_UNIT'][0].upper()
        else:
            self.temp_unit = 0
            self.customParameters['TEMP_UNIT'] = 'C'

        #if 'refresh_token' in self.customParameters:
        #    if self.customParameters['refresh_token'] is not None and self.customParameters['refresh_token'] != "":
        #        self.customData.token['refresh_token'] = self.customParameters['refresh_token']
        oauthSettingsUpdate['scope'] = self.scope
        oauthSettingsUpdate['auth_endpoint'] = 'https://api.netatmo.com/oauth2/authorize'
        oauthSettingsUpdate['token_endpoint'] = 'https://api.netatmo.com/oauth2/token'
        #oauthSettingsUpdate['cloudlink'] = True
        oauthSettingsUpdate['addRedirect'] = True
        self.updateOauthSettings(oauthSettingsUpdate)    
        #logging.debug('Updated oAuth config: {}'.format(self.getOauthSettings()))
        if client_ok and secret_ok:
            self.handleCustomParamsDone = True
            self.poly.Notices.clear()

        #self.updateOauthConfig()
        #self.myParamBoolean = ('myParam' in self.customParametersand self.customParameters['myParam'].lower() == 'true')
        #logging.info(f"My param boolean: { self.myParamBoolean }")
    

    def add_to_parameters(self,  key, value):
        '''add_to_parameters'''
        self.customParameters[key] = value

    def check_parameters(self, key, value):
        '''check_parameters'''
        if key in self.customParameters:
            return(self.customParameters[key]  == value)
        else:
            return(False)
    
    def authendicated(self):
        try:
            logging.debug('authendicated - {}'.format(self.getOauthSettings()))
            self.getAccessToken()
            return(True)
        except ValueError as err:
            logging.warning('Access token is not yet available. Please authenticate.')
            #self.poly.Notices['auth'] = 'Please initiate authentication'
            return (False)
        

    def setOauthScope(self, scope):
        oauthSettingsUpdate = {}
        logging.debug('Set Scope to {}'.format(scope))
        oauthSettingsUpdate['scope'] = str(scope)
        self.updateOauthSettings(oauthSettingsUpdate)
    
    def setOauthName(self, name):
        oauthSettingsUpdate = {} 
        logging.debug('Set name to {}'.format(name))
        oauthSettingsUpdate['name'] = str(name)
        self.updateOauthSettings(oauthSettingsUpdate)
    

    # Call your external service API
    def _callApi(self, method='GET', url=None, body=None):
        # When calling an API, get the access token (it will be refreshed if necessary)
        try:
            accessToken = self.getAccessToken()
        except ValueError as err:
            logging.warning('Access token is not yet available. Please authenticate.')
            self.poly.Notices['auth'] = 'Please initiate authentication'
            return
        if accessToken is None:
            logging.error('Access token is not available')
            return None

        if url is None:
            logging.error('url is required')
            return None

        completeUrl = self.yourApiEndpoint + url

        headers = {
            'Authorization': f"Bearer { accessToken }"
        }

        if method == 'PATCH' and body is None:
            logging.error(f"body is required when using { method } { completeUrl }")
        logging.debug(' call info url={}, header= {}, body = {}'.format(completeUrl, headers, body))

        try:
            if method == 'GET':
                response = requests.get(completeUrl, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(completeUrl, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(completeUrl, headers=headers, json=body)
            elif method == 'POST':
                if body is not None:
                    response = requests.post(completeUrl, headers=headers, json=body)
                else:
                    response = requests.post(completeUrl, headers=headers)
            elif method == 'PUT':
                response = requests.put(completeUrl, headers=headers)

            response.raise_for_status()
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError:
                return response.text

        except requests.exceptions.HTTPError as error:
            logging.error(f"Call { method } { completeUrl } failed: { error }")
            return None

    # Then implement your service specific APIs

### Main node server code

    #def set_temp_unit(self, value):
    #    self.temp_unit = value
#POST "https://api.netatmo.com/api/setroomthermpoint?home_id=1&room_id=2&mode=manual&temp=21&endtime=123"
    def execute_set_setpoint(self, home_id, room_id, Ctemp, mode, t_stop=0):
        logging.debug('execute_setpoint {} {} {}'.format( Ctemp, mode, t_stop))
        home_id_str = urllib.parse.quote_plus(home_id)
        room_id_str = urllib.parse.quote_plus(room_id)
        if mode == 'manual':
            api_str = '/setroomthermpoint?home_id='+home_id_str+'&room_id='+room_id_str+'&mode=manual'+'&temp='+str(Ctemp)
            if t_stop != 0: # do not add stop time 
                api_str=api_str+'&endtime='+str(int(t_stop))
        elif mode == 'max':
            api_str = '/setroomthermpoint?home_id='+home_id_str+'&room_id='+room_id_str+'&mode=max'
            if t_stop == 0: # do not add stop time 
                logging.warning('Warning no stop time specified - setting to 3 hours ')                
                t_stop = int(time.time()+3*60*60)                
            api_str=api_str+'&endtime='+str(int(t_stop))
        else:
            api_str = '/setroomthermpoint?home_id='+home_id_str+'&room_id='+room_id_str+'&mode=home'
            if t_stop != 0: # do not add stop time 
                api_str=api_str+'&endtime='+str(int(t_stop))            
        temp = self._callApi('POST', api_str )
        #logging.debug('execute_set_setpoint return: {} - {}'.format(api_str, temp))
        return(temp)

#POST "https://api.netatmo.com/api/setthermmode?home_id=12345&mode=away&endtime=12345"
    def execute_set_mode(self, home_id, mode, t_stop=0):
        logging.debug('execute_set_mode {} {}'.format( mode, t_stop))
        home_id_str = urllib.parse.quote_plus(home_id)
        api_str = '/setthermmode?home_id='+home_id_str+'&mode='+mode
        if t_stop != 0 and (mode == 'away' or mode == 'hg' ):
            api_str = api_str + '&endtime='+str(int(t_stop))
        temp = self._callApi('POST', api_str )
        logging.debug('execute_set_mode return: {} - {}'.format(api_str, temp))
        return(temp)

    def process_homes_data(self, net_system):
        homes_list = {}
        if net_system and 'homes' in net_system:
            for home in range(0, len(net_system['homes'])):
                tmp = net_system['homes'][home]
                homes_list[tmp['id']]= tmp
        logging.debug('homes list: {}'.format(homes_list))
        return(homes_list)



    def get_homes_info(self):
        logging.debug('get_home_info')
        api_str = '/homesdata'
        temp = self._callApi('GET', api_str )
        if temp and 'body' in temp:
            self.netatmo_systems = temp['body']
            logging.debug(self.netatmo_systems)
            self.homes_list = self.process_homes_data(self.netatmo_systems)
        else:
            logging.error('Failed to retrieve homesdata: {}'.format(temp))
            self.homes_list = getattr(self, 'homes_list', {})
        return(self.homes_list)


    def get_home_status(self, home_id):
        status = {}
        logging.debug('get_home_status {}'.format(home_id))
        try:
            if home_id:
                home_id_str = urllib.parse.quote_plus(home_id)
                #if dev_type == '':
                api_str = '/homestatus?home_id='+str(home_id_str)
                #else:
                #    api_str = '/homestatus?home_id='+str(home_id_str)+'&'+str(dev_type)

                tmp = self._callApi('GET', api_str)
                logging.debug('get_home_status - tmp: {}'.format(tmp))
                if tmp:
                    meas_time = tmp.get('time_server', int(time.time()))                
                    if 'errors' in tmp:
                        status['error'] = tmp['errors']
                    elif 'error' in tmp:
                        status['error'] = tmp['error']

                    if 'body' in tmp and 'home' in tmp['body']:
                        tmp = tmp['body']['home']
                        status[home_id] = home_id #tmp['body']['body']['home']
                        logging.debug('get_home_status - tmp: {}'.format(tmp))
                        if 'modules' in tmp:
                            status['modules'] = {}
                            status['module_types'] = []
                            for indx in range(0,len(tmp['modules'])):
                                status['modules'][tmp['modules'][indx]['id']]= tmp['modules'][indx]
                                status['module_types'].append(tmp['modules'][indx]['type'])
                        logging.debug(status)
                        if 'rooms' in tmp:
                            status['rooms'] = {}
                            #status['module_types'] = []
                            for indx in range(0,len(tmp['rooms'])):              
                                status['rooms'][tmp['rooms'][indx]['id']]=  tmp['rooms'][indx]
                        status['meas_time'] = meas_time
                        self.energy_data[home_id] = status
                        
                    logging.debug('energy_data : {} {}'.format(home_id, self.energy_data ))
                    return(status)
                else:
                    return(None)
        except Exception as e:
            logging.error('Error get home status : {}'.format(e))
            return(None)

    def get_modules(self, home_id):
        '''get_modules'''
        logging.debug('get_modules')
        if home_id in self.homes_list:
            # Find relevan modules
            return(self.homes_list[home_id]['modules'])

    def get_rooms(self, home_id):
        '''get_modules'''
        logging.debug('get_modules')
        if home_id in self.homes_list:
            # Find relevan modules
            return(self.homes_list[home_id]['rooms'])        
        

    def get_module_types(self, home_id):
        '''get_module_types'''
        if home_id in self.homes_list:
            return(self.homes_list[home_id]['module_types'])

    def get_home_name(self, home_id):
        '''get_home_name'''
        if home_id in self.homes_list:
            return(self.homes_list[home_id]['name'])

    

    def module_type (self, type):
        if type in self.GW_modules:
            return('GATEWAY')
        if type in self.valves:
            return('VALVE')
        if type in self.thermostat:
            return('THERMOSTAT')
              
    def get_time_since_last_update_sec(self, home_id):
        timenow = int(time.time())
        if home_id in self.energy_data and 'meas_time' in self.energy_data[home_id]:
            delay_s = int(timenow - self.energy_data[home_id]['meas_time'])
            return(delay_s)
        return(0)

    def get_last_update_time(self, home_id):
        if home_id in self.energy_data and 'meas_time' in self.energy_data[home_id]:
            return(int(self.energy_data[home_id]['meas_time']))
        return(int(time.time()))
    
    def get_room_temp(self, home_id, room_id):
        logging.debug('get_room_temp')
        if home_id in self.energy_data and 'rooms' in self.energy_data[home_id] and room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id].get('therm_measured_temperature'))
        else:
            return(None)
        
    def get_room_setpoint_temp(self, home_id, room_id):
        logging.debug('get_room_set_point_temp')
        if home_id in self.energy_data and 'rooms' in self.energy_data[home_id] and room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id].get('therm_setpoint_temperature'))
        else:
            return(None)


    def get_room_setpoint_mode(self, home_id, room_id):
        logging.debug('get_room_set_point_mode')
        if home_id in self.energy_data and 'rooms' in self.energy_data[home_id] and room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id].get('therm_setpoint_mode'))
        else:
            return(None)
        
    def get_room_online(self, home_id, room_id):
        logging.debug('get_room_online - {} {} {}'.format(home_id, room_id, self.energy_data))
        if home_id in self.energy_data and 'rooms' in self.energy_data[home_id] and room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id].get('reachable', False))
        else:
            return(None)
    
    def get_room_anticipating(self, home_id, room_id):
        logging.debug('get_room_anticipating')
        if home_id in self.energy_data and 'rooms' in self.energy_data[home_id] and room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id].get('anticipating', False))
        else:
            return(None)
        
    def get_room_heat_power_request(self, home_id, room_id):
        logging.debug('get_room_heat_power_request')
        if home_id in self.energy_data and 'rooms' in self.energy_data[home_id] and room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id].get('heating_power_request', 0))
        else:
            return(None)


    def get_room_open_window(self, home_id, room_id):
        logging.debug('get_room_open_window')
        if home_id in self.energy_data and 'rooms' in self.energy_data[home_id] and room_id in self.energy_data[home_id]['rooms']:
            return( self.energy_data[home_id]['rooms'][room_id].get('open_window', False))
        else:
            return(None)


    def get_valve_online(self, home_id, valve_id):
        logging.debug('get_valve_online - data{} {} {}'.format(home_id, valve_id, self.energy_data) )
        if home_id in self.energy_data and 'modules' in self.energy_data[home_id] and valve_id in self.energy_data[home_id]['modules']:
                return( self.energy_data[home_id]['modules'][valve_id].get('reachable', False))
        else:
            return(None)

    def get_valve_bat_state(self, home_id, valve_id):
        logging.debug('get_valve_bat_state')
        if home_id in self.energy_data and 'modules' in self.energy_data[home_id] and valve_id in self.energy_data[home_id]['modules']:
            return( self.energy_data[home_id]['modules'][valve_id].get('battery_state'))
        else:
            return(None)

    def get_valve_bat_level(self, home_id, valve_id):
        logging.debug('get_valve_bat_level')
        if home_id in self.energy_data and 'modules' in self.energy_data[home_id] and valve_id in self.energy_data[home_id]['modules']:
            return( self.energy_data[home_id]['modules'][valve_id].get('battery_level'))
        else:
            return(None)

    def get_valve_rf_strength(self, home_id, valve_id):
        logging.debug('get_valve_rf_strength')
        if home_id in self.energy_data and 'modules' in self.energy_data[home_id] and valve_id in self.energy_data[home_id]['modules']:
            return( self.energy_data[home_id]['modules'][valve_id].get('rf_strength'))
        else:
            return(None)


    def get_energy_homes(self):
        '''    def get_energy_homes(self):'''
        home_list = self.get_homes_info()
        logging.debug('get_energy_homes : {}'.format(home_list))
        self.energy_in_homes = {}
        for home_id in home_list:
            found = False
            home = home_list[home_id]
            logging.debug('homeget_energy_homes: {}'.format(home))
            if 'modules' in home:   
                for module in home['modules']:
                    if module['type'] in self._dev_list:
                        found = True
                if found:
                    self.energy_in_homes[home_id] = home
        logging.debug('self.energy_in_homes {}'.format(self.energy_in_homes))
        return(self.energy_in_homes)

    def get_GW_modules(self, home_id):
        '''get_GW_modules '''
        tmp = self._get_modules(home_id, self.GW_modules)
        logging.debug('get_GW_modules {}'.format(tmp))
        return(self._get_modules(home_id, self.GW_modules))


