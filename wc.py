#!/usr/bin/env python3

import udi_interface
import sys
import time
import requests
import xml.etree.ElementTree as ET
import threading
import yaml
import time  # for renaming delay between calls

# Set up global variables
LOGGER = udi_interface.LOGGER  # Logger for outputting information and errors
Custom = udi_interface.Custom  # For handling custom parameters
polyglot = None
Parameters = None
ip_address = None  # Global IP address for WebControl8 device
username = None  # Global username for authentication
password = None  # Global password for authentication
port = 80  # Default port number for WebControl8 device, initialized globally
n_queue = []  # Queue for node addition
nodes_added = 0  # Counter to track added nodes

# Define the main node class for the WC1 controller
class ControllerNode(udi_interface.Node):
    id = 'controller_node'
    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 25},   # Connection Status (NodeServer Online)
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Heartbeat
        {'driver': 'GV1', 'value': 0, 'uom': 56},  # WebControl8 Name
        {'driver': 'GV2', 'value': 0, 'uom': 56},  # Time
        {'driver': 'GV3', 'value': 0, 'uom': 56},  # Frequency Counter
        {'driver': 'GV4', 'value': 0, 'uom': 56},  # Regular Counter
    ]

    def __init__(self, polyglot, primary, address, name):
        super(ControllerNode, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.heartbeat_value = 1
        self.consecutive_failures = 0
        self.last_name = None
        self.last_datetime = None
        self.gv2_value = 0  # Track current GV2 value
        self.default_name = "WebControl8"  # Default name to use if server name is not available

    def update_node_info(self, root, update_name=False, update_time=False):
        if update_name:
            # Try to get the name from the server, default to the predefined name if it's blank or None
            name = root.find('name').text.strip() if root.find('name') is not None else ""
            if not name:  # If the name is empty, use the default name
                name = self.default_name
            
            LOGGER.debug(f"Updating name: {name}, last_name: {self.last_name}")
            
            # Update driver GV1 with the parsed name or default name
            self.setDriver('GV1', 1 if self.last_name != name else 0, uom=56, text=name, report=True, force=True)
            self.last_name = name
            LOGGER.info(f"WebControl8 Name updated: {name}")
            
            # Rename the main node page using the parsed or default name
            self.rename_main_node(name)

        if update_time:
            datetime = root.find('datetime').text.strip()
            LOGGER.debug(f"Updating datetime: {datetime}")
            self.gv2_value = 1 if self.gv2_value == 0 else 0
            self.setDriver('GV2', self.gv2_value, uom=56, text=datetime, report=True, force=True)
            self.last_datetime = datetime
            LOGGER.info(f"Time updated: {datetime} with GV2 toggle value: {self.gv2_value}")

    def rename_main_node(self, new_name):
        # Only rename the node if the current name differs from the new name
        if self.name != new_name:
            try:
                LOGGER.info(f"Renaming main node {self.address} to {new_name}")
                polyglot.renameNode(self.address, new_name)
                LOGGER.info(f"Node {self.address} renamed to {new_name}")
            except Exception as e:
                LOGGER.error(f"Failed to rename node {self.address}: {e}")
 
    def update_heartbeat(self, success):
        if success:
            self.consecutive_failures = 0
            self.setDriver('GV0', self.heartbeat_value, report=True, force=True)
            self.heartbeat_value = -self.heartbeat_value
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= 2:
                self.setDriver('GV0', 0, report=True, force=True)

    def reset_heartbeat(self):
        self.setDriver('GV0', 0, report=True, force=True)
        self.heartbeat_value = 1

    def query(self, command=None):
        LOGGER.info('Querying WC1 Node: triggering longPoll cycle')
        # Trigger the longPoll manually
        poll('longPoll')

    commands = {
        'QUERY': query,
    }

# Define the class for the AIP1 node
class AIP1Node(udi_interface.Node):
    id = 'aip1_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # aip1
    ]

    def __init__(self, polyglot, primary, address, name):
        super(AIP1Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_aip = None

    def update_aip(self, aip_value, force_update=False):
        if aip_value is not None:
            if force_update or aip_value != self.last_aip:
                self.setDriver('GV0', aip_value, report=True, force=True)
                self.last_aip = aip_value

    def query(self, command=None):
        LOGGER.info('Querying AIP1 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }

# Define the class for the AIP2 node
class AIP2Node(udi_interface.Node):
    id = 'aip2_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # aip2
    ]

    def __init__(self, polyglot, primary, address, name):
        super(AIP2Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_aip = None

    def update_aip(self, aip_value, force_update=False):
        if aip_value is not None:
            if force_update or aip_value != self.last_aip:
                self.setDriver('GV0', aip_value, report=True, force=True)
                self.last_aip = aip_value

    def query(self, command=None):
        LOGGER.info('Querying AIP2 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }

# Define the class for the AIP3 node
class AIP3Node(udi_interface.Node):
    id = 'aip3_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # aip3
    ]

    def __init__(self, polyglot, primary, address, name):
        super(AIP3Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_aip = None

    def update_aip(self, aip_value, force_update=False):
        if aip_value is not None:
            if force_update or aip_value != self.last_aip:
                self.setDriver('GV0', aip_value, report=True, force=True)
                self.last_aip = aip_value

    def query(self, command=None):
        LOGGER.info('Querying AIP3 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }    

# Define the class for the inputs node
class IP1Node(udi_interface.Node):
    id = 'ip1_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # Input ip1
    ]

    def __init__(self, polyglot, primary, address, name):
        super(IP1Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_ip = None

    def update_ip(self, ip_value, force_update=False):
        if ip_value is not None:
            if force_update or ip_value != self.last_ip:
                self.setDriver('GV0', ip_value, report=True, force=True)
                self.last_ip = ip_value

    def query(self, command=None):
        LOGGER.info('Querying IP1 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class IP2Node(udi_interface.Node):
    id = 'ip2_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # Input ip2
    ]

    def __init__(self, polyglot, primary, address, name):
        super(IP2Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_ip = None

    def update_ip(self, ip_value, force_update=False):
        if ip_value is not None:
            if force_update or ip_value != self.last_ip:
                self.setDriver('GV0', ip_value, report=True, force=True)
                self.last_ip = ip_value

    def query(self, command=None):
        LOGGER.info('Querying IP2 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class IP3Node(udi_interface.Node):
    id = 'ip3_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # Input ip3
    ]

    def __init__(self, polyglot, primary, address, name):
        super(IP3Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_ip = None

    def update_ip(self, ip_value, force_update=False):
        if ip_value is not None:
            if force_update or ip_value != self.last_ip:
                self.setDriver('GV0', ip_value, report=True, force=True)
                self.last_ip = ip_value

    def query(self, command=None):
        LOGGER.info('Querying IP3 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class IP4Node(udi_interface.Node):
    id = 'ip4_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # Input ip4
    ]

    def __init__(self, polyglot, primary, address, name):
        super(IP4Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_ip = None

    def update_ip(self, ip_value, force_update=False):
        if ip_value is not None:
            if force_update or ip_value != self.last_ip:
                self.setDriver('GV0', ip_value, report=True, force=True)
                self.last_ip = ip_value

    def query(self, command=None):
        LOGGER.info('Querying IP4 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class IP5Node(udi_interface.Node):
    id = 'ip5_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # Input ip5
    ]

    def __init__(self, polyglot, primary, address, name):
        super(IP5Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_ip = None

    def update_ip(self, ip_value, force_update=False):
        if ip_value is not None:
            if force_update or ip_value != self.last_ip:
                self.setDriver('GV0', ip_value, report=True, force=True)
                self.last_ip = ip_value

    def query(self, command=None):
        LOGGER.info('Querying IP5 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class IP6Node(udi_interface.Node):
    id = 'ip6_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # Input ip6
    ]

    def __init__(self, polyglot, primary, address, name):
        super(IP6Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_ip = None

    def update_ip(self, ip_value, force_update=False):
        if ip_value is not None:
            if force_update or ip_value != self.last_ip:
                self.setDriver('GV0', ip_value, report=True, force=True)
                self.last_ip = ip_value

    def query(self, command=None):
        LOGGER.info('Querying IP6 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class IP7Node(udi_interface.Node):
    id = 'ip7_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # Input ip7
    ]

    def __init__(self, polyglot, primary, address, name):
        super(IP7Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_ip = None

    def update_ip(self, ip_value, force_update=False):
        if ip_value is not None:
            if force_update or ip_value != self.last_ip:
                self.setDriver('GV0', ip_value, report=True, force=True)
                self.last_ip = ip_value

    def query(self, command=None):
        LOGGER.info('Querying IP7 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class IP8Node(udi_interface.Node):
    id = 'ip8_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 56},  # Input ip8
    ]

    def __init__(self, polyglot, primary, address, name):
        super(IP8Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_ip = None

    def update_ip(self, ip_value, force_update=False):
        if ip_value is not None:
            if force_update or ip_value != self.last_ip:
                self.setDriver('GV0', ip_value, report=True, force=True)
                self.last_ip = ip_value

    def query(self, command=None):
        LOGGER.info('Querying IP8 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }

class Op1Node(udi_interface.Node):
    id = 'op1_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Output status op1
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Op1Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_op1 = None

    def update_op1(self, op1_value, force_update=False):
        if op1_value is not None:
            if force_update or op1_value != self.last_op1:
                self.setDriver('GV0', op1_value, report=True, force=True)
                self.last_op1 = op1_value

    def query(self, command=None):
        LOGGER.info('Querying Op1 Node: triggering longPoll cycle')
        poll('longPoll')

    # Define the ON command handler for Op1
    def cmd_on(self, command):
        LOGGER.info('Turning ON Op1')
        try:
            # Send HTTP request to WebControl8 to turn ON the output with authentication
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=1&state=1', 
                                    timeout=5, auth=(username, password))
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op1 is ON")
                    self.update_op1(1, force_update=True)
                else:
                    LOGGER.error("Failed to turn ON Op1, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn ON Op1. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning ON Op1: {e}")

    # Define the OFF command handler for Op1
    def cmd_off(self, command):
        LOGGER.info('Turning OFF Op1')
        try:
            # Send HTTP request to WebControl8 to turn OFF the output with authentication
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=1&state=0', 
                                    timeout=5, auth=(username, password))
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op1 is OFF")
                    self.update_op1(0, force_update=True)
                else:
                    LOGGER.error("Failed to turn OFF Op1, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn OFF Op1. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning OFF Op1: {e}")

    commands = {
        'QUERY': query,
        'DON': cmd_on,  # Map the ON command to cmd_on
        'DOF': cmd_off,  # Map the OFF command to cmd_off
    }

class Op2Node(udi_interface.Node):
    id = 'op2_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Output status op2
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Op2Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_op2 = None

    def update_op2(self, op2_value, force_update=False):
        if op2_value is not None:
            if force_update or op2_value != self.last_op2:
                self.setDriver('GV0', op2_value, report=True, force=True)
                self.last_op2 = op2_value

    def query(self, command=None):
        LOGGER.info('Querying Op2 Node: triggering longPoll cycle')
        poll('longPoll')

    # Define the ON command handler for Op2
    def cmd_on(self, command):
        LOGGER.info('Turning ON Op2')
        try:
            # Send HTTP request to WebControl8 to turn ON the output with authentication
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=2&state=1', 
                                    timeout=5, auth=(username, password))
            
            if response.status_code == 200:
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op2 is ON")
                    self.update_op2(1, force_update=True)
                else:
                    LOGGER.error("Failed to turn ON Op2, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn ON Op2. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning ON Op2: {e}")

    # Define the OFF command handler for Op2
    def cmd_off(self, command):
        LOGGER.info('Turning OFF Op2')
        try:
            # Send HTTP request to WebControl8 to turn OFF the output with authentication
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=2&state=0', 
                                    timeout=5, auth=(username, password))
            
            if response.status_code == 200:
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op2 is OFF")
                    self.update_op2(0, force_update=True)
                else:
                    LOGGER.error("Failed to turn OFF Op2, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn OFF Op2. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning OFF Op2: {e}")

    commands = {
        'QUERY': query,
        'DON': cmd_on,  # Map the ON command to cmd_on
        'DOF': cmd_off,  # Map the OFF command to cmd_off
    }

class Op3Node(udi_interface.Node):
    id = 'op3_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Output status op3
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Op3Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_op3 = None

    def update_op3(self, op3_value, force_update=False):
        if op3_value is not None:
            if force_update or op3_value != self.last_op3:
                self.setDriver('GV0', op3_value, report=True, force=True)
                self.last_op3 = op3_value

    def query(self, command=None):
        LOGGER.info('Querying Op3 Node: triggering longPoll cycle')
        poll('longPoll')

    # Define the ON command handler for Op3
    def cmd_on(self, command):
        LOGGER.info('Turning ON Op3')
        try:
            # Send HTTP request to WebControl8 to turn ON the output with authentication
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=3&state=1', 
                                    timeout=5, auth=(username, password))
            
            if response.status_code == 200:
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op3 is ON")
                    self.update_op3(1, force_update=True)
                else:
                    LOGGER.error("Failed to turn ON Op3, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn ON Op3. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning ON Op3: {e}")

    # Define the OFF command handler for Op3
    def cmd_off(self, command):
        LOGGER.info('Turning OFF Op3')
        try:
            # Send HTTP request to WebControl8 to turn OFF the output with authentication
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=3&state=0', 
                                    timeout=5, auth=(username, password))
            
            if response.status_code == 200:
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op3 is OFF")
                    self.update_op3(0, force_update=True)
                else:
                    LOGGER.error("Failed to turn OFF Op3, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn OFF Op3. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning OFF Op3: {e}")

    commands = {
        'QUERY': query,
        'DON': cmd_on,  # Map the ON command to cmd_on
        'DOF': cmd_off,  # Map the OFF command to cmd_off
    }

class Op4Node(udi_interface.Node):
    id = 'op4_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Output status op4
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Op4Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_op4 = None

    def update_op4(self, op4_value, force_update=False):
        if op4_value is not None:
            if force_update or op4_value != self.last_op4:
                self.setDriver('GV0', op4_value, report=True, force=True)
                self.last_op4 = op4_value

    def query(self, command=None):
        LOGGER.info('Querying Op4 Node: triggering longPoll cycle')
        poll('longPoll')

    # Define the ON command handler
    def cmd_on(self, command):
        LOGGER.info('Turning ON Op4')
        try:
            # Send HTTP request to WebControl8 to turn ON the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=4&state=1', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op4 is ON")
                    self.update_op4(1, force_update=True)
                else:
                    LOGGER.error("Failed to turn ON Op4, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn ON Op4. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning ON Op4: {e}")

    # Define the OFF command handler
    def cmd_off(self, command):
        LOGGER.info('Turning OFF Op4')
        try:
            # Send HTTP request to WebControl8 to turn OFF the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=4&state=0', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op4 is OFF")
                    self.update_op4(0, force_update=True)
                else:
                    LOGGER.error("Failed to turn OFF Op4, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn OFF Op4. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning OFF Op4: {e}")

    commands = {
        'QUERY': query,
        'DON': cmd_on,  # Map the ON command to cmd_on
        'DOF': cmd_off,  # Map the OFF command to cmd_off
    }


class Op5Node(udi_interface.Node):
    id = 'op5_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Output status op5
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Op5Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_op5 = None

    def update_op5(self, op5_value, force_update=False):
        if op5_value is not None:
            if force_update or op5_value != self.last_op5:
                self.setDriver('GV0', op5_value, report=True, force=True)
                self.last_op5 = op5_value

    def query(self, command=None):
        LOGGER.info('Querying Op5 Node: triggering longPoll cycle')
        poll('longPoll')

    # Define the ON command handler
    def cmd_on(self, command):
        LOGGER.info('Turning ON Op5')
        try:
            # Send HTTP request to WebControl8 to turn ON the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=5&state=1', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op5 is ON")
                    self.update_op5(1, force_update=True)
                else:
                    LOGGER.error("Failed to turn ON Op5, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn ON Op5. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning ON Op5: {e}")

    # Define the OFF command handler
    def cmd_off(self, command):
        LOGGER.info('Turning OFF Op5')
        try:
            # Send HTTP request to WebControl8 to turn OFF the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=5&state=0', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op5 is OFF")
                    self.update_op5(0, force_update=True)
                else:
                    LOGGER.error("Failed to turn OFF Op5, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn OFF Op5. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning OFF Op5: {e}")

    commands = {
        'QUERY': query,
        'DON': cmd_on,  # Map the ON command to cmd_on
        'DOF': cmd_off,  # Map the OFF command to cmd_off
    }


class Op6Node(udi_interface.Node):
    id = 'op6_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Output status op6
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Op6Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_op6 = None

    def update_op6(self, op6_value, force_update=False):
        if op6_value is not None:
            if force_update or op6_value != self.last_op6:
                self.setDriver('GV0', op6_value, report=True, force=True)
                self.last_op6 = op6_value

    def query(self, command=None):
        LOGGER.info('Querying Op6 Node: triggering longPoll cycle')
        poll('longPoll')

    # Define the ON command handler
    def cmd_on(self, command):
        LOGGER.info('Turning ON Op6')
        try:
            # Send HTTP request to WebControl8 to turn ON the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=6&state=1', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op6 is ON")
                    self.update_op6(1, force_update=True)
                else:
                    LOGGER.error("Failed to turn ON Op6, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn ON Op6. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning ON Op6: {e}")

    # Define the OFF command handler
    def cmd_off(self, command):
        LOGGER.info('Turning OFF Op6')
        try:
            # Send HTTP request to WebControl8 to turn OFF the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=6&state=0', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op6 is OFF")
                    self.update_op6(0, force_update=True)
                else:
                    LOGGER.error("Failed to turn OFF Op6, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn OFF Op6. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning OFF Op6: {e}")

    commands = {
        'QUERY': query,
        'DON': cmd_on,  # Map the ON command to cmd_on
        'DOF': cmd_off,  # Map the OFF command to cmd_off
    }

class Op7Node(udi_interface.Node):
    id = 'op7_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Output status op7
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Op7Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_op7 = None

    def update_op7(self, op7_value, force_update=False):
        if op7_value is not None:
            if force_update or op7_value != self.last_op7:
                self.setDriver('GV0', op7_value, report=True, force=True)
                self.last_op7 = op7_value

    def query(self, command=None):
        LOGGER.info('Querying Op7 Node: triggering longPoll cycle')
        poll('longPoll')

    # Define the ON command handler
    def cmd_on(self, command):
        LOGGER.info('Turning ON Op7')
        try:
            # Send HTTP request to WebControl8 to turn ON the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=7&state=1', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op7 is ON")
                    self.update_op7(1, force_update=True)
                else:
                    LOGGER.error("Failed to turn ON Op7, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn ON Op7. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning ON Op7: {e}")

    # Define the OFF command handler
    def cmd_off(self, command):
        LOGGER.info('Turning OFF Op7')
        try:
            # Send HTTP request to WebControl8 to turn OFF the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=7&state=0', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op7 is OFF")
                    self.update_op7(0, force_update=True)
                else:
                    LOGGER.error("Failed to turn OFF Op7, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn OFF Op7. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning OFF Op7: {e}")

    commands = {
        'QUERY': query,
        'DON': cmd_on,  # Map the ON command to cmd_on
        'DOF': cmd_off,  # Map the OFF command to cmd_off
    }


class Op8Node(udi_interface.Node):
    id = 'op8_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Output status op8
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Op8Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_op8 = None

    def update_op8(self, op8_value, force_update=False):
        if op8_value is not None:
            if force_update or op8_value != self.last_op8:
                self.setDriver('GV0', op8_value, report=True, force=True)
                self.last_op8 = op8_value

    def query(self, command=None):
        LOGGER.info('Querying Op8 Node: triggering longPoll cycle')
        poll('longPoll')

    # Define the ON command handler
    def cmd_on(self, command):
        LOGGER.info('Turning ON Op8')
        try:
            # Send HTTP request to WebControl8 to turn ON the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=8&state=1', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op8 is ON")
                    self.update_op8(1, force_update=True)
                else:
                    LOGGER.error("Failed to turn ON Op8, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn ON Op8. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning ON Op8: {e}")

    # Define the OFF command handler
    def cmd_off(self, command):
        LOGGER.info('Turning OFF Op8')
        try:
            # Send HTTP request to WebControl8 to turn OFF the output
            response = requests.get(f'http://{ip_address}:{port}/api/setttloutput.cgi?output=8&state=0', 
                                    auth=(username, password), timeout=5)
            
            if response.status_code == 200:
                # Parse response (assuming success confirmation in the response content)
                if 'success' in response.text.lower():
                    LOGGER.info("Server confirmed Op8 is OFF")
                    self.update_op8(0, force_update=True)
                else:
                    LOGGER.error("Failed to turn OFF Op8, server did not confirm success")
            elif response.status_code == 401:
                LOGGER.warning("Check Username and/or Password")
            else:
                LOGGER.error(f"Failed to turn OFF Op8. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Exception occurred while turning OFF Op8: {e}")

    commands = {
        'QUERY': query,
        'DON': cmd_on,  # Map the ON command to cmd_on
        'DOF': cmd_off,  # Map the OFF command to cmd_off
    }

class Temp1Node(udi_interface.Node):
    id = 'temp1_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts1 (Default to Fahrenheit)
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat1 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp1Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp1 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }
    
class Temp1Node(udi_interface.Node):
    id = 'temp1_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts1 (Default to Fahrenheit)
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat1 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp1Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp1 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class Temp2Node(udi_interface.Node):
    id = 'temp2_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts2
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat2 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp2Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp2 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }

class Temp3Node(udi_interface.Node):
    id = 'temp3_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts3
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat3 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp3Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp3 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class Temp4Node(udi_interface.Node):
    id = 'temp4_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts4
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat4 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp4Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp4 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class Temp5Node(udi_interface.Node):
    id = 'temp5_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts5
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat5 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp5Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp5 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class Temp6Node(udi_interface.Node):
    id = 'temp6_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts6
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat6 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp6Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp6 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class Temp7Node(udi_interface.Node):
    id = 'temp7_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts7
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat7 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp7Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp7 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }


class Temp8Node(udi_interface.Node):
    id = 'temp8_node'
    drivers = [
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Temperature ts8
        {'driver': 'GV1', 'value': 0, 'uom': 25},  # tstat8 status
    ]

    def __init__(self, polyglot, primary, address, name):
        super(Temp8Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_temp = None
        self.last_tstat = None

    # Update temp status
    def update_temp_and_status(self, temp_value, tstat_value, uom, force_update=False):
        if temp_value is not None:
            if force_update or temp_value != self.last_temp:
                self.setDriver('GV0', temp_value, report=True, force=True, uom=uom)
                self.last_temp = temp_value

        if tstat_value is not None:  # Ensure tstat_value is not None before calling lower()
            tstat_status = 1 if tstat_value.lower() == "ok" else 0
        else:
            tstat_status = 0  # Default value if None

        if force_update or tstat_status != self.last_tstat:
            self.setDriver('GV1', tstat_status, report=True, force=True)
            self.last_tstat = tstat_status

    def query(self, command=None):
        LOGGER.info('Querying Temp8 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {
        'QUERY': query,
    }

# Define the class for the variables node
class Var1Node(udi_interface.Node):
    id = 'var1_node'
    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 56}]  # var1

    def __init__(self, polyglot, primary, address, name):
        super(Var1Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_var = None

    def update_var(self, var_value, force_update=False):
        if var_value is not None:
            if force_update or var_value != self.last_var:
                self.setDriver('GV0', var_value, report=True, force=True)
                self.last_var = var_value

    def query(self, command=None):
        LOGGER.info('Querying Var1 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {'QUERY': query}

class Var2Node(udi_interface.Node):
    id = 'var2_node'
    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 56}]  # var2

    def __init__(self, polyglot, primary, address, name):
        super(Var2Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_var = None

    def update_var(self, var_value, force_update=False):
        if var_value is not None:
            if force_update or var_value != self.last_var:
                self.setDriver('GV0', var_value, report=True, force=True)
                self.last_var = var_value

    def query(self, command=None):
        LOGGER.info('Querying Var2 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {'QUERY': query}

class Var3Node(udi_interface.Node):
    id = 'var3_node'
    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 56}]  # var3

    def __init__(self, polyglot, primary, address, name):
        super(Var3Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_var = None

    def update_var(self, var_value, force_update=False):
        if var_value is not None:
            if force_update or var_value != self.last_var:
                self.setDriver('GV0', var_value, report=True, force=True)
                self.last_var = var_value

    def query(self, command=None):
        LOGGER.info('Querying Var3 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {'QUERY': query}

class Var4Node(udi_interface.Node):
    id = 'var4_node'
    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 56}]  # var4

    def __init__(self, polyglot, primary, address, name):
        super(Var4Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_var = None

    def update_var(self, var_value, force_update=False):
        if var_value is not None:
            if force_update or var_value != self.last_var:
                self.setDriver('GV0', var_value, report=True, force=True)
                self.last_var = var_value

    def query(self, command=None):
        LOGGER.info('Querying Var4 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {'QUERY': query}

class Var5Node(udi_interface.Node):
    id = 'var5_node'
    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 56}]  # var5

    def __init__(self, polyglot, primary, address, name):
        super(Var5Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_var = None

    def update_var(self, var_value, force_update=False):
        if var_value is not None:
            if force_update or var_value != self.last_var:
                self.setDriver('GV0', var_value, report=True, force=True)
                self.last_var = var_value

    def query(self, command=None):
        LOGGER.info('Querying Var5 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {'QUERY': query}

class Var6Node(udi_interface.Node):
    id = 'var6_node'
    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 56}]  # var6

    def __init__(self, polyglot, primary, address, name):
        super(Var6Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_var = None

    def update_var(self, var_value, force_update=False):
        if var_value is not None:
            if force_update or var_value != self.last_var:
                self.setDriver('GV0', var_value, report=True, force=True)
                self.last_var = var_value

    def query(self, command=None):
        LOGGER.info('Querying Var6 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {'QUERY': query}

class Var7Node(udi_interface.Node):
    id = 'var7_node'
    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 56}]  # var7

    def __init__(self, polyglot, primary, address, name):
        super(Var7Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_var = None

    def update_var(self, var_value, force_update=False):
        if var_value is not None:
            if force_update or var_value != self.last_var:
                self.setDriver('GV0', var_value, report=True, force=True)
                self.last_var = var_value

    def query(self, command=None):
        LOGGER.info('Querying Var7 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {'QUERY': query}

class Var8Node(udi_interface.Node):
    id = 'var8_node'
    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 56}]  # var8

    def __init__(self, polyglot, primary, address, name):
        super(Var8Node, self).__init__(polyglot, primary, address, name)
        self.polyglot = polyglot
        self.last_var = None

    def update_var(self, var_value, force_update=False):
        if var_value is not None:
            if force_update or var_value != self.last_var:
                self.setDriver('GV0', var_value, report=True, force=True)
                self.last_var = var_value

    def query(self, command=None):
        LOGGER.info('Querying Var8 Node: triggering longPoll cycle')
        poll('longPoll')

    commands = {'QUERY': query}

# Function to fetch temperature, variable, input, AIP, and output data from the WebControl8 device
def fetch_data():
    try:
        # Check if ip_address and port are set before proceeding
        if not ip_address or not port:
            LOGGER.error("IP address or port not set. Cannot fetch data.")
            return None, [None] * 8, [None] * 8, [None] * 8, [None] * 8, [None] * 3, [None] * 8, 17, False

        # Prepare authentication using username and password, if provided
        auth = (username, password) if username and password else None

        # Construct the URL using the provided IP address and port, and make the request
        url = f'http://{ip_address}:{port}/getall.cgi'
        LOGGER.info(f'Fetching data from URL: {url}')
        response = requests.get(url, timeout=5, auth=auth)

        # Check if the response from the WebControl8 device was successful (HTTP 200 OK)
        if response.status_code == 200:
            LOGGER.info('Successfully fetched data from the WebControl8 device.')
            root = ET.fromstring(response.content)  # Parse the XML response

            # Initialize arrays to store values for temperatures, variables, inputs, AIPs, and outputs
            ts_values = [None] * 8    # Temperature sensors (ts1 to ts8)
            tstat_values = [None] * 8 # Temperature statuses (tstat1 to tstat8)
            var_values = [None] * 8   # Variables (var1 to var8)
            ip_values = [None] * 8    # Inputs (ip1 to ip8)
            aip_values = [None] * 3   # AIPs (aip1 to aip3)
            output_values = [None] * 8 # Outputs (op1 to op8)

            uom = 17  # Default UOM is Fahrenheit (17)

            # Iterate through each temperature sensor and status (ts1-ts8 and tstat1-tstat8)
            for i in range(1, 9):
                # Fetch temperature (e.g., ts1, ts2,...ts8)
                temp_element = root.find(f'ts{i}')
                if temp_element is not None:
                    temp_str = temp_element.text.strip()  # Get the temperature string
                    if temp_str.endswith('F'):
                        ts_values[i - 1] = float(temp_str.split()[0])  # Convert to Fahrenheit
                    elif temp_str.endswith('C'):
                        ts_values[i - 1] = float(temp_str.split()[0])  # Convert to Celsius
                        uom = 4  # Update UOM to Celsius (4)
                    else:
                        ts_values[i - 1] = None  # Handle invalid/missing temperature

                # Fetch temperature status (e.g., tstat1, tstat2,...tstat8)
                tstat_element = root.find(f'tstat{i}')
                tstat_values[i - 1] = tstat_element.text.strip() if tstat_element is not None else None

                # Fetch variable values (e.g., var1, var2,...var8)
                var_element = root.find(f'var{i}')
                var_values[i - 1] = float(var_element.text.strip()) if var_element is not None else None

                # Fetch input values (e.g., ip1, ip2,...ip8)
                ip_element = root.find(f'ip{i}')
                ip_values[i - 1] = float(ip_element.text.strip()) if ip_element is not None else None

                # Fetch output values (e.g., op1, op2,...op8)
                output_element = root.find(f'op{i}')
                output_values[i - 1] = float(output_element.text.strip()) if output_element is not None else None

            # Fetch AIP values (only for aip1, aip2, and aip3)
            for i in range(1, 4):
                aip_element = root.find(f'aip{i}')
                aip_values[i - 1] = float(aip_element.text.strip()) if aip_element is not None else None

            # Return all parsed values, along with the XML root and UOM
            return root, ts_values, tstat_values, var_values, ip_values, aip_values, output_values, uom, True

        # If the response was unauthorized (401), log a warning and return default values
        elif response.status_code == 401:
            LOGGER.warning("Unauthorized access. Check username and/or password.")
            return None, [None] * 8, [None] * 8, [None] * 8, [None] * 8, [None] * 3, [None] * 8, 17, False

        # For any other HTTP error, log the status code and return default values
        else:
            LOGGER.error(f"Failed to fetch data from WebControl8 device. Status code: {response.status_code}")
            return None, [None] * 8, [None] * 8, [None] * 8, [None] * 8, [None] * 3, [None] * 8, 17, False

    # Handle network-related exceptions (e.g., timeout, connection errors)
    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Error fetching data: {str(e)}")
        return None, [None] * 8, [None] * 8, [None] * 8, [None] * 8, [None] * 3, [None] * 8, 17, False

# Function to handle polling (runs periodically)
def poll(polltype):
    global ip_address

    # Check if IP address is not set or is using the default invalid one
    if ip_address == 'Enter WebControl IP Address' or ip_address is None:
        LOGGER.warning('Enter a Valid WebControl IP Address.')
        return

    # Proceed with the normal polling process once the IP is valid
    wc1_node = polyglot.getNode('wc1_node')

    wc1_aip1_node = polyglot.getNode('aip1')
    wc1_aip2_node = polyglot.getNode('aip2')
    wc1_aip3_node = polyglot.getNode('aip3')

    temp_nodes = [polyglot.getNode(f'temp{i}') for i in range(1, 9)]
    var_nodes = [polyglot.getNode(f'var{i}') for i in range(1, 9)]
    ip_nodes = [polyglot.getNode(f'ip{i}') for i in range(1, 9)]
    op_nodes = [polyglot.getNode(f'op{i}') for i in range(1, 9)]

    # Fetch data from WebControl8 device
    root, ts_values, tstat_values, var_values, ip_values, aip_values, output_values, uom, success = fetch_data()

    if polltype == 'longPoll':
        LOGGER.info('Executing longPoll tasks...')

        # Update Temp1 to Temp8 nodes
        for i in range(8):
            if temp_nodes[i] is not None:
                temp_nodes[i].update_temp_and_status(ts_values[i], tstat_values[i], uom, force_update=True)

        # Update Var1 to Var8 nodes
        for i in range(8):
            if var_nodes[i] is not None:
                var_nodes[i].update_var(var_values[i], force_update=True)

        # Update IP1 to IP8 nodes
        for i in range(8):
            if ip_nodes[i] is not None:
                ip_nodes[i].update_ip(ip_values[i], force_update=True)

        # Update AIP1 to AIP3 nodes
        if wc1_aip1_node is not None:
            wc1_aip1_node.update_aip(aip_values[0], force_update=True)
        if wc1_aip2_node is not None:
            wc1_aip2_node.update_aip(aip_values[1], force_update=True)
        if wc1_aip3_node is not None:
            wc1_aip3_node.update_aip(aip_values[2], force_update=True)

        # Update OP1 to OP8 nodes
        for i in range(8):
            if op_nodes[i] is not None:
                op_nodes[i].setDriver('GV0', output_values[i], report=True, force=True)

        # Update WC1 Node (main controller)
        if wc1_node is not None and success and root is not None:
            wc1_node.update_node_info(root, update_name=True, update_time=True)

            # Update counters (GV3 and GV4)
            fcounter = root.find('fcounter').text.strip() if root.find('fcounter') is not None else 0
            counter = root.find('counter').text.strip() if root.find('counter') is not None else 0
            wc1_node.setDriver('GV3', int(fcounter), report=True, force=True)
            wc1_node.setDriver('GV4', int(counter), report=True, force=True)

            wc1_node.update_heartbeat(success)
            wc1_node.setDriver('ST', 1, report=True, force=True)
        elif not success:
            wc1_node.setDriver('ST', 0, report=True, force=True)

    elif polltype == 'shortPoll':
        LOGGER.info('Executing shortPoll tasks...')
        # Short poll: update only if values have changed
        for i in range(8):
            if temp_nodes[i] is not None:
                temp_nodes[i].update_temp_and_status(ts_values[i], tstat_values[i], uom, force_update=False)

        for i in range(8):
            if var_nodes[i] is not None:
                var_nodes[i].update_var(var_values[i], force_update=False)

        for i in range(8):
            if ip_nodes[i] is not None:
                ip_nodes[i].update_ip(ip_values[i], force_update=False)

        if wc1_aip1_node is not None:
            wc1_aip1_node.update_aip(aip_values[0], force_update=False)
        if wc1_aip2_node is not None:
            wc1_aip2_node.update_aip(aip_values[1], force_update=False)
        if wc1_aip3_node is not None:
            wc1_aip3_node.update_aip(aip_values[2], force_update=False)

        for i in range(8):
            if op_nodes[i] is not None:
                op_nodes[i].setDriver('GV0', output_values[i], report=True, force=False)

        # Check if GV3 and GV4 values have changed before updating
        if wc1_node is not None and success and root is not None:
            fcounter = root.find('fcounter').text.strip() if root.find('fcounter') is not None else 0
            counter = root.find('counter').text.strip() if root.find('counter') is not None else 0

            # Update GV3 (fcounter) only if it has changed
            if int(fcounter) != wc1_node.getDriver('GV3'):
                wc1_node.setDriver('GV3', int(fcounter), report=True, force=True)

            # Update GV4 (counter) only if it has changed
            if int(counter) != wc1_node.getDriver('GV4'):
                wc1_node.setDriver('GV4', int(counter), report=True, force=True)

            wc1_node.update_node_info(root, update_name=False, update_time=True)
            wc1_node.update_heartbeat(success)
            wc1_node.setDriver('ST', 1, report=True, force=True)

# Function to initialize custom parameters
def initialize_params():
    params_doc = (
        "Custom Parameters:\n"
        "- ip_address: The IP address of the WebControl8 device.\n"
        "- port: The port number to access the WebControl8 device (default is 80).\n"
        "- username: The username for accessing the WebControl8 device (optional).\n"
        "- password: The password for accessing the WebControl8 device (optional).\n"
        "- devlist: YAML configuration for renaming nodes. Paste your YAML here."
    )
    polyglot.setCustomParamsDoc(params_doc)
    LOGGER.info("Custom parameters initialized.")

# Function to process custom parameters and apply node renaming
def on_custom_params(params):
    global ip_address, username, password, port
    Parameters.load(params)

    # Handle IP address
    if 'ip_address' not in Parameters or not Parameters['ip_address']:
        ip_address = 'Enter WebControl IP Address'
        Parameters['ip_address'] = ip_address
        LOGGER.info(f'Initialized ip_address to default value ({ip_address}).')
    else:
        new_ip = Parameters['ip_address']
        if new_ip != ip_address:
            ip_address = new_ip
            LOGGER.info(f'Using user-defined IP address: {ip_address}')
            polyglot.updateProfile()
            poll('longPoll')

    # Handle port (default to 80)
    if 'port' not in Parameters or not Parameters['port']:
        port = 80
        Parameters['port'] = port
        LOGGER.info(f'Initialized port to default value (80).')
    else:
        new_port = Parameters['port']
        if new_port != port:
            port = new_port
            LOGGER.info(f'Using user-defined port: {port}')

    # Handle username (default to 'admin')
    if 'username' not in Parameters or not Parameters['username']:
        username = 'admin'
        Parameters['username'] = username
        LOGGER.info('Initialized username to default value (admin).')
    else:
        username = Parameters['username']
        LOGGER.info(f'Using user-defined username: {username}')

    # Handle password (default to 'password')
    if 'password' not in Parameters or not Parameters['password']:
        password = 'password'
        Parameters['password'] = password
        LOGGER.info('Initialized password to default value (password).')
    else:
        password = Parameters['password']
        LOGGER.info(f'Using user-defined password.')

    # Handle devlist (default to 'add yaml single line string for node names')
    if 'devlist' not in Parameters or not Parameters['devlist']:
        devlist = 'add yaml single line string for node names'
        Parameters['devlist'] = devlist
        LOGGER.info(f'Initialized devlist to default value ({devlist}).')
    else:
        devlist = Parameters['devlist']
        LOGGER.info(f'Using user-defined devlist: {devlist}')

    # Prepare a dictionary to batch renaming requests
    rename_operations = {}

    # Process YAML from devlist (node renaming) only if devlist is not default or blank
    if devlist != 'add yaml single line string for node names' and devlist.strip():
        try:
            yaml_data = yaml.safe_load(devlist)
            
            if isinstance(yaml_data, dict):  # Check if yaml_data is a dictionary
                # Gather rename operations in a batch
                for node_key, node_name in yaml_data.items():
                    node = polyglot.getNode(node_key)
                    if node:
                        # Only rename if the name is different
                        if node.name != node_name:
                            rename_operations[node.address] = node_name
                    else:
                        LOGGER.warning(f"Node with key {node_key} not found.")
            else:
                LOGGER.error("devlist does not contain valid YAML data for node renaming.")
        except yaml.YAMLError as e:
            LOGGER.error(f"Failed to parse YAML in devlist: {e}")
    else:
        LOGGER.info("Skipping YAML parsing due to default or blank devlist value.")

    # Add additional dynamic renaming logic (for temp, var, ip, op nodes)
    for i in range(1, 9):
        temp_name_key = f'temp{i}_name'
        temp_node = polyglot.getNode(f'temp{i}')
        if temp_name_key in Parameters and temp_node:
            new_name = Parameters[temp_name_key]
            if temp_node.name != new_name:
                rename_operations[temp_node.address] = new_name

        var_name_key = f'var{i}_name'
        var_node = polyglot.getNode(f'var{i}')
        if var_name_key in Parameters and var_node:
            new_name = Parameters[var_name_key]
            if var_node.name != new_name:
                rename_operations[var_node.address] = new_name

        ip_name_key = f'ip{i}_name'
        ip_node = polyglot.getNode(f'ip{i}')
        if ip_name_key in Parameters and ip_node:
            new_name = Parameters[ip_name_key]
            if ip_node.name != new_name:
                rename_operations[ip_node.address] = new_name

        op_name_key = f'op{i}_name'
        op_node = polyglot.getNode(f'op{i}')
        if op_name_key in Parameters and op_node:
            new_name = Parameters[op_name_key]
            if op_node.name != new_name:
                rename_operations[op_node.address] = new_name

    # Add AIP node renames
    for i in range(1, 4):
        aip_name_key = f'aip{i}_name'
        aip_node = polyglot.getNode(f'aip{i}')
        if aip_name_key in Parameters and aip_node:
            new_name = Parameters[aip_name_key]
            if aip_node.name != new_name:
                rename_operations[aip_node.address] = new_name

    # Now process the rename operations in batch, with a delay to avoid overloading the system
    for node_address, new_name in rename_operations.items():
        try:
            polyglot.renameNode(node_address, new_name)
            LOGGER.info(f"Renamed node {node_address} to {new_name}")
            
            # Introduce a small delay (e.g., 500 milliseconds) between rename requests
            time.sleep(0.5)  # 500ms delay
        except Exception as e:
            LOGGER.error(f"Failed to rename node {node_address}: {e}")

    LOGGER.info(f"Processed {len(rename_operations)} renaming operations.")

# Handler for the ADDNODEDONE event
def node_added_handler(data):
    global nodes_added
    address = data['address']
    LOGGER.info(f"Node added with address: {address}")

    node_addresses = [
        'wc1_node', 'wc1_temps', 'wc1_inputs', 'wc1_aip', 'temp1', 'temp2', 'temp3', 'temp4', 'temp5', 'temp6', 'temp7', 'temp8',
        'var1', 'var2', 'var3', 'var4', 'var5', 'var6', 'var7', 'var8', 'op2'  # Added op2 node address
    ]

    # If the added address is in the expected list, increment the nodes_added counter
    if address in node_addresses:
        nodes_added += 1
        LOGGER.info(f"Node {address} added ({nodes_added}/{len(node_addresses)} nodes added).")
        
        # Check if all nodes have been added
        if nodes_added == len(node_addresses):
            LOGGER.info("All nodes added. Scheduling initial poll with threading.Timer.")
            threading.Timer(5, initial_poll).start()

# Function to handle the node server's shutdown process
def stop():
    LOGGER.info("Node server stopping, setting ST to False and heartbeat to 0")
    nodes = polyglot.getNodes()
    for node in nodes.values():
        node.setDriver('ST', 0, report=True, force=True)
        if node.id == 'wc1_node':
            node.reset_heartbeat()
        time.sleep(0.5)

    polyglot.stop()

# Function to perform the initial poll with delay
def initial_poll():
    LOGGER.info("Performing initial poll after startup delay")
    poll('longPoll')

# Main script entry point
if __name__ == "__main__": 
    try:
        polyglot = udi_interface.Interface([]) 
        polyglot.start('1.0.0')

        Parameters = Custom(polyglot, 'customparams')

        # Initialize custom parameters before setting Polyglot to ready
        initialize_params()

        # Subscribe to custom parameter changes
        polyglot.subscribe(polyglot.CUSTOMPARAMS, on_custom_params)

        # Subscribe to Polyglot events
        polyglot.subscribe(polyglot.ADDNODEDONE, node_added_handler)
        polyglot.subscribe(polyglot.STOP, stop)
        polyglot.subscribe(polyglot.POLL, poll)

        polyglot.ready()

        # Update profile first and delay node addition until the profile is fully updated
        LOGGER.info("Updating profile before adding nodes.")
        polyglot.updateProfile()

        # Use threading.Timer to delay node additions until profile is updated
        def add_nodes():
            # Add the main controller node
            wc1_node = ControllerNode(polyglot, 'wc1_node', 'wc1_node', 'WebControl8')
            polyglot.addNode(wc1_node)

            # Add Temp1 to Temp8 nodes dynamically
            for i in range(1, 9):
                temp_name_key = f'temp{i}_name'
                if temp_name_key in Parameters:
                    temp_name = Parameters[temp_name_key]
                else:
                    temp_name = f'Temp {i}'  # Default name
                
                temp_node = globals()[f'Temp{i}Node'](polyglot, 'wc1_node', f'temp{i}', temp_name)
                polyglot.addNode(temp_node)
                LOGGER.info(f"Added node {temp_node.address} with name: {temp_name}")

                time.sleep(0.5)  # 500ms delay between adding each node

            # Add Var1 to Var8 nodes dynamically
            for i in range(1, 9):
                var_name_key = f'var{i}_name'
                if var_name_key in Parameters:
                    var_name = Parameters[var_name_key]
                else:
                    var_name = f'Variable {i}'  # Default name
                
                var_node = globals()[f'Var{i}Node'](polyglot, 'wc1_node', f'var{i}', var_name)
                polyglot.addNode(var_node)
                LOGGER.info(f"Added node {var_node.address} with name: {var_name}")

                time.sleep(0.5)  # 500ms delay between adding each node

            # Add AIP1 to AIP3 nodes dynamically
            for i in range(1, 4):
                aip_name_key = f'aip{i}_name'
                if aip_name_key in Parameters:
                    aip_name = Parameters[aip_name_key]
                else:
                    aip_name = f'AIP {i}'  # Default name
                
                aip_node = globals()[f'AIP{i}Node'](polyglot, 'wc1_node', f'aip{i}', aip_name)
                polyglot.addNode(aip_node)
                LOGGER.info(f"Added node {aip_node.address} with name: {aip_name}")

                time.sleep(0.5)  # 500ms delay between adding each node

            # Add IP1 to IP8 nodes dynamically
            for i in range(1, 9):
                ip_node = globals()[f'IP{i}Node'](polyglot, 'wc1_node', f'ip{i}', f'Input {i}')
                polyglot.addNode(ip_node)
                time.sleep(0.5)  # 500ms delay between adding each node

            # Add OP1 to OP8 nodes dynamically
            for i in range(1, 9):
                op_name_key = f'op{i}_name'
                if op_name_key in Parameters:
                    op_name = Parameters[op_name_key]
                else:
                    op_name = f'Output {i}'  # Default name
                
                op_node = globals()[f'Op{i}Node'](polyglot, 'wc1_node', f'op{i}', op_name)
                polyglot.addNode(op_node)
                LOGGER.info(f"Added node {op_node.address} with name: {op_name}")

                time.sleep(0.5)  # 500ms delay between adding each node

        # Delay node addition by 5 seconds to ensure profile is fully updated
        threading.Timer(5, add_nodes).start()

        # Keep the program running indefinitely
        polyglot.runForever()

    except Exception as e:
        LOGGER.error(f"Exception occurred: {e}")
        stop()  # Call the stop method to handle shutdown