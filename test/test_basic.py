from datetime import datetime

from twisted.internet import reactor, protocol
from twisted.internet import defer
from twisted.trial import unittest
from twistedfcp.protocol import (FreenetClientProtocol, IdentifiedMessage, 
                                 logging)
from twistedfcp.util import sequence
from twistedfcp.error import PutException, FetchException, ProtocolException

from simple_server import TestServerProtocol, TestServerFactory

logging.basicConfig(filename="twistedfcp.log", 
                    filemode="w", 
                    level=logging.DEBUG)

class ClientTest(unittest.TestCase):
    "Test that connects to some server before starting."

    def setUp(self):
        creator = protocol.ClientCreator(reactor, FreenetClientProtocol)
        def cb(client):
            if hasattr(self, "fcp_timeout"):
                client.timeout = self.fcp_timeout
            self.client = client

        connected = creator.connectTCP('localhost', self.port)
        return connected.addCallback(cb)

    def tearDown(self):
        shutdowns = []
        if hasattr(self, "client"):
            self.client.transport.loseConnection()
        if hasattr(self, "server"):
            shutdowns.append(defer.maybeDeferred(self.server.stopListening))

        return defer.gatherResults(shutdowns)

class LoopbackBaseTest(ClientTest):
    """
    All tests of this type will spawn a ``TestServerFactory`` and connect to it.
    This is the quintessential unit test with mocked external dependencies.

    """
    fcp_timeout = 5
    port = TestServerProtocol.port

    def setUp(self):
        self.server = reactor.listenTCP(self.port, TestServerFactory())
        return ClientTest.setUp(self)

class IntegrationBaseTest(ClientTest):
    """
    This is a real "integration test" that connects directly to the Freenet node
    running on ``localhost``.

    """
    fcp_timeout = 10 * 60
    port = FreenetClientProtocol.port

    def __init__(self, *args):
        ClientTest.__init__(self, *args)
        self.timeout = 1000000

FCPBaseTest = LoopbackBaseTest

class ClientHelloTest(FCPBaseTest):
    "Tests that the Freenet node responds to a ClientHello message."
    @sequence
    def test_hello(self):
        msg = yield self.client.deferred['NodeHello']
        self.assertEquals(msg['FCPVersion'], '2.0')

class GetPutTest(FCPBaseTest):
    "Tests get/put messages to the Freenet node."
    @sequence
    def test_ksk(self):
        _ = yield self.client.deferred['NodeHello']
        now = datetime.now()
        uri = "KSK@" + now.strftime("%Y-%m-%d-%H-%M")
        # First put.
        testdata = "Testing 123..."
        response = yield self.client.put_direct(uri, testdata)
        self.assertEqual(response["URI"], uri)
        # Then get.
        response = yield self.client.get_direct(uri)
        # Finally check the data.
        self.assertEqual(response["Data"], testdata)

    @sequence
    def test_chk(self):
        _ = yield self.client.deferred['NodeHello']
        uri = "CHK@"
        testdata = "Testing CHK put..."
        response = yield self.client.put_direct(uri, testdata)
        uri = response["URI"]
        response = yield self.client.get_direct(uri)
        self.assertEqual(response["Data"], testdata)

    @sequence
    def test_ssk(self):
        _ = yield self.client.deferred['NodeHello']
        public, private = yield self.client.get_ssk_keypair()
        fragment = "test-update/test-fragment"
        public += fragment
        private += fragment
        testdata = "Testing SSK put..."
        _ = yield self.client.put_direct(private, testdata)
        response = yield self.client.get_direct(public[:-1])
        self.assertEqual(response["Data"], testdata)

class PeerListTest(FCPBaseTest):
    "Tests that the user can list clients from the node."
    @sequence
    def test_peer_list(self):
        _ = yield self.client.deferred['NodeHello']
        clients = yield self.client.get_all_peers()
        # Ideally the client should be connected to 12 peers. Expect at least
        # half that.
        self.assertTrue(len(clients) > 6)
        for client in (dict(l) for l in clients):
            self.assertTrue(client['identity'] is not None)

class GetPutErrorTest(FCPBaseTest):
    "Tests error modes for the get/put messages to the node."
    @sequence
    def test_ksk_errors(self):
        "Test that getting an invalid KSK throws an exception."
        _ = yield self.client.deferred['NodeHello']
        exceptionThrown = None
        try:
            uri = "KSK@not-a-valid-ksk-at-all"
            response = yield self.client.get_direct(uri)
        except FetchException as e:
            self.assertEqual(e.code, 13)
        else:
            self.fail("No error thrown when getting a non-existant KSK!")
