from twisted.internet import reactor, protocol
from twisted.trial import unittest
from twistedfcp.protocol import fcp_protocol

class ClientHelloTest(unittest.TestCase):

    def log_message(self, msg):
        self.assertEquals(msg['FCPVersion'], '2.0')
 
    def test_hello(self):
        creator = protocol.ClientCreator(reactor, fcp_protocol) 
        def cb(client):
            self.client = client
            defer = client.deferred['NodeHello']
            return defer.addCallback(self.log_message)

        defer = creator.connectTCP('localhost', fcp_protocol.port)
        return defer.addCallback(cb)
