from datetime import datetime

from twisted.internet import reactor, protocol
from twisted.trial import unittest
from twistedfcp.protocol import FreenetClientProtocol, IdentifiedMessage

def withClient(f):
    def _inner(self):
        creator = protocol.ClientCreator(reactor, FreenetClientProtocol)
        def cb(client):
            self.client = client
            return f(self, client)
        defer = creator.connectTCP('localhost', FreenetClientProtocol.port)
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

class FCPBaseTest(unittest.TestCase):
    "We always want to clean up after the test is done."
    def tearDown(self):
        if self.client is not None:
            self.client.transport.loseConnection()

class ClientHelloTest(FCPBaseTest):
    @withClient
    @sequence
    def test_hello(self, client):
        msg = yield client.deferred['NodeHello']
        self.assertEquals(msg['FCPVersion'], '2.0')

class GetPutTest(FCPBaseTest):
    @withClient
    @sequence
    def test_ksk(self, client):
        _ = yield client.deferred['NodeHello']
        now = datetime.now()
        uri = "KSK@" + now.strftime("%Y-%m-%d-%H-%M")
        # First put.
        testdata = "Testing 123..."
        put = IdentifiedMessage("ClientPut", [("Verbosity", 1), ("URI", uri)])
        client.sendMessage(put, data=testdata)
        response = yield client.deferred["PutSuccessful"]
        self.assertEqual(response["Identifier"], put["Identifier"])
        # Then get.
        get = IdentifiedMessage("ClientGet", [("URI", uri)])
        client.sendMessage(get)
        response = yield client.deferred["AllData"]
        
        # Finally check the data.
        self.assertEqual(response["Identifier"], get["Identifier"])
        self.assertEqual(response["Data"], testdata)

