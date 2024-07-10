import requests
import udi_interface
from datetime import datetime

LOGGER = udi_interface.LOGGER

class WcTestNode(udi_interface.Node):
    def __init__(self, controller, primary, address, name, wc_ip):
        super(WcTestNode, self).__init__(controller, primary, address, name)
        self.wc_ip = wc_ip

    def start(self):
        self.query()

    def longPoll(self):
        self.query()

    def query(self):
        try:
            url = f'http://{self.wc_ip}/temp.xml'
            response = requests.get(url, auth=('admin', 'admin'))
            if response.status_code == 200:
                temp1 = self.parse_temp1(response.text)
                self.report_temp1(temp1)
            else:
                LOGGER.error(f'Error {response.status_code} fetching data from {self.wc_ip}')
        except Exception as e:
            LOGGER.error(f'Exception: {str(e)}')

    def parse_temp1(self, xml_data):
        # Parsing logic to extract Temp1 value from the xml_data
        # Assuming xml_data has a tag <temp1>value</temp1>
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        temp1 = root.find('temp1').text
        return float(temp1)

    def report_temp1(self, temp1):
        self.setDriver('GV0', temp1)

    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 17}]
    id = 'WcTestNode'
    commands = {'QUERY': query}

