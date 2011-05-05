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
from error import FetchException

class FreenetClientProtocol(protocol.Protocol):
    """
    Definition of the Freenet Client Protocol. 

    """
    port = 9481
    def __init__(self):
        self.deferred = defaultdict(Deferred)
        self.sessions = defaultdict(Deferred)

    def connectionMade(self):
        "On connection, sends a FCP ClientHello message."
        self.sendMessage(ClientHello)

    def dataReceived(self, data):
        "Parses in received packets until none remain."
        partial = data
        while partial: 
            partial = self._parseOne(partial)
    
    def _parseOne(self, data):
        """
        Parses a single packet from ``data`` and handles it. Returns the remnant
        of the ``data`` after the first message has been removed.

        """
        safe_index = lambda x: data.index(x) if x in data else len(data)
        endHeader = min(safe_index(p) for p in ['\nData\n', '\nEndMessage\n'])
        header, data = data[:endHeader], data[endHeader:]

        header = header.split('\n')
        messageType = header[0]
        message = dict(line.split('=') for line in header[1:])
        if data.startswith('\nData\n'):
            l = int(message['DataLength'])
            data = data[len('\nData\n'):]
            message['Data'], data = data[:l], data[l:]
        else:
            data = data[len('\nEndMessage\n'):]
        logging.info("Received {0}".format(messageType))
        logging.debug(message)
        self._process(message, messageType)
        return data

    def _process(self, message, messageType):
        if messageType in self.deferred:
            deferred = self.deferred[messageType]
            deferred.callback(message)
        if 'Identifier' in message: 
            session_id = message['Identifier']
            if session_id in self.sessions:
                defer = self.sessions[session_id]
                del self.sessions[session_id]
                result = defer.callback(Message(messageType, message.items()))

    def sendMessage(self, message, data=None):
        """
        Sends a single ``message`` to the server. If ``data`` is specified, it
        gets tacked on to the end of the message and a ``DataLength`` field is
        added to the message arguments.

        """
        self.transport.write(message.name)
        self.transport.write('\n')
        for key, value in message.args:
            self.transport.write(str(key))
            self.transport.write('=')
            self.transport.write(str(value))
            self.transport.write('\n')

        if not data:
            self.transport.write('EndMessage\n')
            logging.info("Sent {0}".format(message.name))
            logging.debug(message.args)
        else:
            self.transport.write('DataLength={0}\n'.format(len(data)))
            self.transport.write('Data\n')
            self.transport.write(data)
            logging.info("Sent {0} (data length={1})".format(message.name, 
                                                             len(data)))
            logging.debug(message.args)

    def get_direct(self, uri):
        done = Deferred()
        get = IdentifiedMessage("ClientGet", [("URI", uri)])
        session_id = get.id
        def process(message):
            if message.name == "AllData":
                done.callback(message)
            elif message.name == "GetFailed":
                done.errback(FetchFailed(message))
            else:
                self.sessions[session_id].addCallback(process)

        self.sessions[session_id].addCallback(process)
        self.sendMessage(get)
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

