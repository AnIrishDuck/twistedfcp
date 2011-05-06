"""
Defines errors that can be thrown by the Freenet Node. These exceptions 
transform raw messages into Python ``Exception`` objects.

"""
from twisted.python.failure import Failure

class FCPException(Failure, Exception):
    "Base exception for all FCP errors."

    def __init__(self, error_msg):
        self.code = int(error_msg['Code'])
        self.msg = error_msg['CodeDescription']
        text = "Get failed with code {code}: {msg}" 
        Exception.__init__(self, text.format(code=self.code, msg=self.msg))

    def __repr__(self): return "{0}: {1}".format(type(self), self.msg)

    def __str__(self): return self.__repr__()

class FetchException(FCPException):
    "An exception indicating a prior fetch operation has failed."
    message = "GetFailed"

class PutException(FCPException):
    "An exception indicating a prior put operation has failed."
    message = "PutFailed"

class ProtocolException(FCPException):
    "An exception indicating a problem with the Freenet protocol."
    message = "ProtocolError"

class IdentifierException(FCPException):
    """
    An exception indicating that the client is attempting to reuse an 
    Identifier.
    """
    message = "IdentifierCollision"

class UnknownNodeException(FCPException):
    "An exception indicating that the specified node is not known."
    message = "UnknownNodeIdentifier"

class UnknownPeerNoteException(FCPException):
    "An exception indicating that the specified peer note type is not known."
    message = "UnknonwPeerNoteType"

error_dict = dict((klass.message, klass) 
                  for klass in FCPException.__subclasses__())
