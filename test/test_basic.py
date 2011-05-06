from datetime import datetime

from twisted.internet import reactor, protocol
from twisted.trial import unittest
from twistedfcp.protocol import (FreenetClientProtocol, IdentifiedMessage, 
                                 logging)
from twistedfcp.util import sequence
from twistedfcp.error import PutException, FetchException, ProtocolException

logging.basicConfig(filename="twistedfcp.log", 
                    filemode="w", 
                    level=logging.DEBUG)

def withClient(f):
    "Obtains a client and passes it to the wrapped function as an argument."
    def _inner(self):
        creator = protocol.ClientCreator(reactor, FreenetClientProtocol)
        def cb(client):
            self.client = client
            return f(self, client)
        defer = creator.connectTCP('localhost', FreenetClientProtocol.port)
        return defer.addCallback(cb)
    return _inner

class FCPBaseTest(unittest.TestCase):
    "We always want to clean up after the test is done."

    def __init__(self, *args):
        FCPBaseTest.__init__(self, *args)
        self.timeout = 5 * 60

    def tearDown(self):
        if self.client is not None:
            self.client.transport.loseConnection()

class ClientHelloTest(FCPBaseTest):
    "Tests that the Freenet node responds to a ClientHello message."
    @withClient
    @sequence
    def test_hello(self, client):
        msg = yield client.deferred['NodeHello']
        self.assertEquals(msg['FCPVersion'], '2.0')

class GetPutTest(FCPBaseTest):
    "Tests get/put messages to the Freenet node."
    @withClient
    @sequence
    def test_ksk(self, client):
        _ = yield client.deferred['NodeHello']
        now = datetime.now()
        uri = "KSK@" + now.strftime("%Y-%m-%d-%H-%M")
        # First put.
        testdata = "Testing 123..."
        response = yield client.put_direct(uri, testdata)
        self.assertEqual(response["URI"], uri)
        # Then get.
        response = yield client.get_direct(uri)
        # Finally check the data.
        self.assertEqual(response["Data"], testdata)

class GetPutErrorTest(FCPBaseTest):
    "Tests error modes for the get/put messages to the node."
    @withClient
    @sequence
    def test_ksk_errors(self, client):
        "Test that getting an invalid KSK throws an exception."
        try:
            _ = yield client.deferred['NodeHello']
            exceptionThrown = None
            try:
                response = yield client.get_direct("KSK@not-a-valid-ksk-at-all")
            except FetchException as e:
                self.assertEqual(e.code, 30)
            else:
                self.fail("No error thrown when getting a non-existant KSK!")

            try:
                response = yield client.put_direct("BS@NOT-A-URI", 
                                                   "this should fail")
            except PutException as e:
                self.assertEqual(e.code, 1)
            else:
                self.fail("No error thrown when using an invalid URI on put!")
        except Exception as e:
            self.fail("Exception thrown: {0}".format(e))
