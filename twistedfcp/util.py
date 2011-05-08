"""
Defines utility functions for the ``twistedfcp`` module.

"""
import logging
from twisted.protocols.basic import LineReceiver

def sequence(f):
    """
    Sequences a generator function through deferreds. Takes each sent 
    ``Deferred`` and attaches a callback to it that sends the generator
    function the results when they arrive. Continues to recursively do this
    until the generator function is exhausted.

    """
    def _inner(*args):
        gen = f(*args)
        continue_defer = lambda d: d.addCallbacks(cb, er)

        def cb(*args):
            if len(args) == 1: args = args[0]
            try:
                return continue_defer(gen.send(args))
            except StopIteration:
                pass

        def er(msg):
            try:
                return continue_defer(gen.throw(msg))
            except StopIteration:
                pass 

        return continue_defer(gen.next())
    return _inner

class MessageBasedProtocol(LineReceiver):
    """
    Defines a protocol that parses freenet-style messages. These messages take
    the following form::
        
        NodeHello
        FCPVersion=2.0
        ConnectionIdentifier=754595fc35701d76096d8279d15c57e6
        Version=Fred,0.7,1.0,1231
        Node=Fred
        NodeLanguage=ENGLISH
        ExtRevision=23771
        Build=1231
        Testnet=false
        ExtBuild=26
        CompressionCodecs=3 - GZIP(0), BZIP2(1), LZMA(2)
        Revision=@custom@
        EndMessage

    Note that it is possible for messages to end with a ``Data`` line instead
    of an ``EndMessage`` line. These messages will be followed by a binary data
    string whose length was specified previously by a ``DataLength`` field.
    Example::
        
        AllData
        Identifier=Request Number One
        DataLength=37261 // length of data
        StartupTime=1189683889
        CompletionTime=1189683889
        Metadata.ContentType=text/plain;charset=utf-8
        Data
        <37261 bytes of data>

    """
    def __init__(self):
        self.delimiter = "\n"
        self.reset()

    def reset(self):
        "Resets this protocol to its original state (waiting for a new message)"
        self.dataReceived = self.dataReceived
        self.lineReceived = self.new_message
        self.messageName = None
        self.message = {}

    def new_message(self, line):
        "In this state, the protocol treats the line as the message name."
        self.messageName = line
        self.lineReceived = self.key_value

    def key_value(self, line):
        "In this state, the protocol treats the line as a ``key=value`` pair."
        if line == "EndMessage":
            self.end_message()
        elif line == "Data":
            if 'DataLength' not in self.message:
                text = ('Encountered a "Data" ending in a message without '
                        'a "DataLength" key')
                raise MalformedMessageException(text)
            else:
                self.message['Data'] = []
                self.dataCount = 0
                self.setRawMode()
        else:
            kv = line.split('=')
            if len(kv) != 2:
                text = 'Bad line encountered: "{0}" (expected "key=value")'
                raise MalformedMessageException(text.format(line))
            self.message.update([kv])

    def rawDataReceived(self, data):
        """
        In this state we parse the final data in the message. 
        
        .. note::
            This state can only be reached when this instance is in "raw mode".

        """
        self.dataCount += len(data)
        self.message["Data"].append(data)
        expected = int(self.message["DataLength"])
        if self.dataCount >= expected:
            all_data = ''.join(self.message["Data"])
            self.message["Data"] = all_data[:expected]
            self.end_message()
            self.setLineMode(all_data[expected:])

    def end_message(self):
        "Process a fully received message and resets state."
        logging.info("Received {0}.".format(self.messageName))
        logging.debug(str(self.message))
        self.message_received(self.messageName, self.message)
        self.reset()

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
