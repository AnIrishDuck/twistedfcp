"""
Defines errors that can be thrown by the Freenet Node. These exceptions 
transform raw messages into Python ``Exception`` objects.

"""
from twisted.python.failure import Failure

class FetchException(Failure, Exception):
    "An exception indicating a prior fetch operation has failed."

    def __init__(self, error_msg):
        self.code = int(error_msg['Code'])
        self.msg = error_msg['CodeDescription']
        text = "Get failed with code {code}: {msg}" 
        Exception.__init__(self, text.format(code=self.code, msg=self.msg))

    def __repr__(self): return "{0}: {1}".format(type(self), self.msg)

    def __str__(self): return self.__repr__()
