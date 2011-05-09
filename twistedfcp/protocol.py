"""
Twisted implementation of the Freenet Client Protocol. Defines a class, 
``FreenetClientProtocol`` that can connect to the Freenet server.

Similarly, defines a factory ``FCPFactory`` that produces 
``FreenetClientProtocol`` objects when connected to a reactor.

"""
import struct
import logging

from collections import defaultdict
from twisted.internet import reactor, protocol
from twisted.internet.defer import Deferred
from message import Message, IdentifiedMessage, ClientHello
from error import NodeTimeout, Failure, error_dict
from util import MessageBasedProtocol

class FreenetClientProtocol(MessageBasedProtocol):
    """
    Defines a twisted implementation of the Freenet Client Protocol. There are
    several important things to note about the internals of this class: 
    
    - You can wait for specific message types by putting a ``Deferred`` in the
      corresponding key of the ``deferred`` instance variable::

        self.deferred['ClientHello'].addCallback(my_callback)

    - You can wait for a message associated with a specific session (where all
      messages associated with it have the same attached ``Identifier`` field)
      by putting a ``Deferred`` in the corresponding key of the ``sessions``
      instance variable::

        self.sessions['Request101'].addCallback(session_callback)

    - When a ``Deferred`` attached to this class by either the ``deferred`` or 
      ``sessions`` variable fires, it is automatically removed, meaning that the
      callback must re-attach if it wants to receive further notifications.

    - All sessions will be forcibly ended (with a ``NodeTimeout`` errback) after
      a set period of time. This period of time is set by default to 
      ``FreenetClientProtocol.default_timeout`` and can be changed by setting
      ``self.timeout`` for a given instance.

    """
    default_timeout = 10 * 60
    port = 9481

    def __init__(self):
        MessageBasedProtocol.__init__(self)
        self.deferred = defaultdict(Deferred)
        self.sessions = defaultdict(Deferred)
        self.timeout = self.default_timeout

    def connectionMade(self):
        "On connection, sends a FCP ClientHello message."
        self.sendMessage(ClientHello)

    def message_received(self, messageType, messageItems):
        "Processes the received message, firing the necessary deferreds."
        message = Message(messageType, messageItems.items())
        if message.name in self.deferred:
            deferred = self.deferred[message.name]
            del self.deferred[message.name]
            deferred.callback(message)
        if 'Identifier' in message: 
            session_id = message['Identifier']
            if session_id in self.sessions:
                deferred = self.sessions[session_id]
                del self.sessions[session_id]
                result = deferred.callback(message)

    def do_session(self, msg, handler, data=None):
        """
        Wraps the given message processing function ``f`` in session handling
        code. Ends the session if it lasts longer than ``self.timeout`` seconds.

        """
        done = Deferred()
        session_id = msg.id

        def timeout():
            text = 'The node timed out on session "{0}"'
            logging.error(text.format(session_id))
            del self.sessions[session_id]
            done.errback(NodeTimeout())

        timeout = reactor.callLater(self.timeout, timeout)

        def callback(a):
            if a.name in error_dict.keys():
                exception = error_dict[a.name]
                timeout.cancel()
                done.errback(exception(a))
            else:
                result = handler(a)
                if result:
                    timeout.cancel()
                    done.callback(result)
                else:
                    self.sessions[session_id].addCallback(callback) 

        self.sessions[session_id].addCallback(callback)
        self.sendMessage(msg, data)

        return done

    def get_direct(self, uri):
        """
        Does a direct get of the given ``uri`` (data will be returned in the
        body of the message in the ``Data`` field. Returns a ``Deferred`` event
        that will fire when the final ``AllData`` message arrives.

        """
        get = IdentifiedMessage("ClientGet", [("URI", uri), ("Verbosity", 1)])
        def process(message):
            if message.name == "AllData":
                return message

        return self.do_session(get, process)

    def put_direct(self, uri, data):
        """
        Does a direct put to the given ``uri`` (data will be sent directly in
        the body of the message in the ``Data`` field). Returns a ``Deferred``
        even that will fire when the final ``PutSuccessful`` message arrives,
        or will errback when a ``PutFailed`` message arrives.

        """
        put = IdentifiedMessage("ClientPut", [("URI", uri), ("Verbosity", 1)])
        def process(message):
            if message.name == "PutSuccessful":
                return message

        return self.do_session(put, process, data)

    def get_ssk_keypair(self):
        """
        Requests a generated SSK keypair from the Freenet Node. This keypair can
        then be used either as a SSK or USK in future get and put requests. 

        The returned value is a ``Deferred`` that will be called with a 
        list containing first the public, then the private key.

        """
        gen = IdentifiedMessage("GenerateSSK", [])
        def process(message):
            if message.name == "SSKKeypair":
                public = message["InsertURI"]
                private = message["RequestURI"]
                return [public, private]

        return self.do_session(gen, process)

    def get_all_peers(self):
        list_msg = Message("ListPeers", [])
        peers = []
        done = Deferred()

        def node_info(message):
            peers.append(message.args)
            self.deferred["Peer"].addCallback(node_info)

        def end_list(message):
            del self.deferred["Peer"]
            done.callback(peers)

        self.deferred["Peer"].addCallback(node_info)
        self.deferred["EndListPeers"].addCallback(end_list)
        self.sendMessage(list_msg)
        return done

class FCPFactory(protocol.Factory):
    "A protocol factory that uses FCP."
    protocol = FreenetClientProtocol

def main():
    factory = protocol.ClientFactory()
    factory.protocol = fcp_test_protocol
    reactor.connectTCP('localhost', 9481, factory)
    reactor.run()

if __name__ == '__main__':
    main()

