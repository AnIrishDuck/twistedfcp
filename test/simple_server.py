import hashlib
from twisted.internet.protocol import ServerFactory

from twistedfcp.message import Message, IdentifiedMessage
from twistedfcp.util import MessageBasedProtocol

sha = hashlib.sha224

class TestServerProtocol(MessageBasedProtocol):
    """
    Test server that responds to messages. Simulates a freenet store by simply
    storing/retrieving from a dictionary of URIs.

    """
    port = 9999 

    def __init__(self):
        MessageBasedProtocol.__init__(self)
        self.store = {}

    def message_received(self, messageName, messageItems):
        message = Message(messageName, messageItems.items())
        if hasattr(self, message.name):
            f = getattr(self, message.name)
            f(message)

    def ClientHello(self, message):
        self.sendMessage(Message("NodeHello", [("FCPVersion", "2.0")]))

    def ClientGet(self, message):
        uri = message["URI"]
        id_pair = ("Identifier", message["Identifier"])
        if uri in self.store:
            msg = Message("AllData", [id_pair])
            self.sendMessage(msg, data=self.store[uri])
        else:
            msg = Message("GetFailed", 
                          [id_pair,
                           ("Code", 13), 
                           ("CodeDescription", "Data not found")])
            self.sendMessage(msg)

    def ClientPut(self, message):
        uri = message["URI"]
        if uri.split("@", 1)[0] == 'CHK':
            uri = "CHK@{0}".format(sha(message["Data"]).hexdigest())
        
        self.store[uri] = message["Data"]
        self.sendMessage(Message("PutSuccessful", 
                                 [("Identifier", message["Identifier"]),
                                  ("URI", uri)]))

    def ListPeers(self, message):
        for x in xrange(5):
            msg = Message("Peer", [("identity", hex(x))])
            self.sendMessage(msg)

        self.sendMessage(Message("EndListPeers", []))

class TestServerFactory(ServerFactory):
    protocol = TestServerProtocol
