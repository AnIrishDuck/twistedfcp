"""
Defines errors that can be thrown by the Freenet Node. These exceptions 
transform raw messages into Python ``Exception`` objects.

"""
from twisted.python.failure import Failure

class FCPException(Exception):
    "Base exception for all FCP errors."

class MalformedMessageException(FCPException):
    "Indicates that the Freenet node sent a malformed message to the client."
    def __init__(self):
        FCPException.__init__(self, "The message sent was malformed.")

class NodeTimeout(FCPException):
    "Indicates that the Freenet node has timed out while waiting for a result."
    def __init__(self): 
        FCPException.__init__(self, "The node timed out.")

class MessageException(FCPException):
    "Base class for all exceptions that are raised by a specific FCP message."
    def __init__(self, error_msg):
        self.code = int(error_msg['Code'])
        self.msg = error_msg['CodeDescription']
        text = "Get failed with code {code}: {msg}" 
        Exception.__init__(self, text.format(code=self.code, msg=self.msg))

    def __repr__(self): return "{0}: {1}".format(type(self), self.msg)

    def __str__(self): return self.__repr__()

class FetchException(MessageException):
    "Indicates a prior fetch operation has failed."
    message = "GetFailed"

class PutException(MessageException):
    "Indicates a prior put operation has failed."
    message = "PutFailed"

class ProtocolException(MessageException):
    "Indicates a problem with the Freenet protocol."
    message = "ProtocolError"

class IdentifierException(MessageException):
    "Indicates that the client is attempting to reuse an Identifier."
    message = "IdentifierCollision"

class UnknownNodeException(MessageException):
    "Indicates that the specified node is not known."
    message = "UnknownNodeIdentifier"

class UnknownPeerNoteException(MessageException):
    "Indicates that the specified peer note type is not known."
    message = "UnknonwPeerNoteType"

error_dict = dict((klass.message, klass) 
                  for klass in MessageException.__subclasses__())
