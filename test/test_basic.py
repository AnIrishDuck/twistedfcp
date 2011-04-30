from twisted.internet import reactor, protocol
from twisted.trial import unittest
from twistedfcp.protocol import fcp_protocol

def withClient(f):
    def _inner(self):
        creator = protocol.ClientCreator(reactor, fcp_protocol)
        def cb(client):
            self.client = client
            return f(self, client)
        defer = creator.connectTCP('localhost', fcp_protocol.port)
        return defer.addCallback(cb)
    return _inner

class ClientHelloTest(unittest.TestCase):
    @withClient
    def test_hello(self, client):
        defer = client.deferred['NodeHello']
        def check_version(msg):
            self.assertEquals(msg['FCPVersion'], '2.0')
        return defer.addCallback(check_version)

    def tearDown(self):
        if self.client is not None:
            self.client.transport.loseConnection()
