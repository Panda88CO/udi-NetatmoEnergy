#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""


import time
import traceback
import re

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)


#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface


class udiNetatmoEnergyValve(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, update_ISY_data, node_queue, wait_for_node_done, battery2ISY, con_state2ISY

    def __init__(self, polyglot, primary, address, name, myNetatmo, home,  valve_id):
        super().__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.myNetatmo= myNetatmo
        self.valve_id = valve_id
        self.home_id = home['id']
        self._home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'valve'
        self.drivers = [

            {'driver' : 'GV0', 'value': 99,  'uom':25}, 
            {'driver' : 'GV2', 'value': 99,  'uom':25}, 
            {'driver' : 'GV1', 'value': 99,  'uom':25},       
            {'driver' : 'ST', 'value': 99,  'uom':25}, 
            ]

        self.node_ready = False
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} valve Node'.format(self.name))  
        time.sleep(1)
        self.n_queue = []  
        self.nodeDefineDone = True
        self.node_ready = True

    
    


    def start(self):
        logging.debug('Executing udiNetatmoEnergyValve start')
        self.updateISYdrivers()        


   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')

        #data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Valve module data:')
        if self.node is not None:
            if self.myNetatmo.get_valve_online(self.home_id, self.valve_id):
                self.node.setDriver('ST',1)
                self.node.setDriver('GV2', round(self.myNetatmo.get_valve_bat_level(self.home_id, self.valve_id)/1000, 2), True, True, 72)
                self.node.setDriver('GV0', self.battery2ISY(self.myNetatmo.get_valve_bat_state(self.home_id, self.valve_id)))
                self.node.setDriver('GV1', int(-self.myNetatmo.get_valve_rf_strength(self.home_id, self.valve_id)), True, True, 131)
            else:
                self.node.setDriver('GV2', 99, True, False, 25 )
                self.node.setDriver('GV0', 99)
                self.node.setDriver('GV1', 99, True, False, 25 )
                self.node.setDriver('ST', 0)
                

    def update(self, command = None):
        self.myNetatmo.self.myNetatmo.get_home_status(self._home['id'])
        self.update_ISY_data()


    commands = {        
                'UPDATE': update,
              }
