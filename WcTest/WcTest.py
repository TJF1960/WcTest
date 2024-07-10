#!/usr/bin/env python3
"""

import udi_interface
import time
from nodes.WcTestNode import WcTestNode

LOGGER = udi_interface.LOGGER

class WcTest(udi_interface.Interface):
    id = 'WcTest'
    def __init__(self, polyglot):
        super(WcTest, self).__init__(polyglot)
        self.name = 'WcTest'
        self.wc_ip = self.getCustomParam('WcIp')
        self.poly.addNode(WcTestNode(self, self.address, 'wc_test_node', 'WebControl Temp1', self.wc_ip))

    def start(self):
        LOGGER.info('WcTest Node Server starting...')
        self.heartbeat()
        self.query()

    def heartbeat(self):
        LOGGER.debug('Sending Heartbeat')
        self.poly.reportCmd("DON")
        time.sleep(30)
        self.heartbeat()

    def query(self):
        for node in self.nodes:
            node.query()

    def longPoll(self):
        for node in self.nodes:
            node.longPoll()

if __name__ == "__main__":
    poly = udi_interface.Interface([WcTest])
    poly.start()
    WcTest(poly)
    poly.runForever()

