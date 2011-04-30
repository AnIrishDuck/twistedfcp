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

def sequence(f):
    """
    Sequences a generator function through deferreds. Takes each sent 
    ``Deferred`` and attaches a callback to it that sends the generator
    function the results when they arrive. Continues to recursively do this
    until the generator function is exhausted.

    """
    def _inner(*args):
        gen = f(*args)
        first = gen.next()
        def cb(*args):
            if len(args) == 1: args = args[0]
            try:
                d = gen.send(args)
                return d.addCallback(cb)
            except StopIteration:
                pass
    
        return first.addCallback(cb)
    
    return _inner

class ClientHelloTest(unittest.TestCase):
    @withClient
    @sequence
    def test_hello(self, client):
        msg = yield client.deferred['NodeHello']
        self.assertEquals(msg['FCPVersion'], '2.0')

    def tearDown(self):
        if self.client is not None:
            self.client.transport.loseConnection()
