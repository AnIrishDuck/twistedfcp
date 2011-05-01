from collections import defaultdict
from twisted.internet import reactor, protocol
from twisted.internet.defer import Deferred
import struct
from message import IdentifiedMessage, ClientHello

class FreenetClientProtocol(protocol.Protocol):
    port = 9481
    def __init__(self):
        self.deferred = defaultdict(Deferred)

    def connectionMade(self):
        self.sendMessage(ClientHello)

    def dataReceived(self, data):
        partial = data
        while partial: 
            partial = self.parseOne(partial)
    
    def parseOne(self, data):
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
        print "Received {0}".format(messageType)
        print message
        if messageType in self.deferred:
            deferred = self.deferred[messageType]
            if isinstance(deferred, Deferred): 
                deferred.callback(message)
            else:
                deferred[message['Identifier']].callback(message)

        return data

    def sendMessage(self, message, data=None):
        self.transport.write(message.name)
        self.transport.write('\n')
        for key, value in message.args:
            self.transport.write(str(key))
            self.transport.write('=')
            self.transport.write(str(value))
            self.transport.write('\n')
        if not data:
            self.transport.write('EndMessage\n')
            print "Sent {0}".format(message.name)
        else:
            self.transport.write('DataLength={0}\n'.format(len(data)))
            self.transport.write('Data\n')
            self.transport.write(data)
            print "Sent {0} (data length={1})".format(message.name, len(data))

class FCPFactory(protocol.Factory):
    protocol = FreenetClientProtocol


def main():
    factory = protocol.ClientFactory()
    factory.protocol = fcp_test_protocol
    reactor.connectTCP('localhost', 9481, factory)
    reactor.run()

if __name__ == '__main__':
    main()

