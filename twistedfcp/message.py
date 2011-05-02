"""
Defines messages sent through the Freenet Client Protocol.

"""

class Message(object):
    "A simple message with a name and arguments."

    def __init__(self, name, args):
        self.name = name
        self.args = args

class IdentifiedMessage(Message):
    "A message with an ``Identifier`` that is used to identify sessions."
    id = 0
    def __init__(self, *args):
        Message.__init__(self, *args)
        self.args.append(["Identifier", self.unused_identifier])

    def __getitem__(self, el):
        for k, v in self.args:
            if k == el: return v

        raise IndexError("The key {0} is not in the message.".format(el))

    @property
    def unused_identifier(self):
        "Returns an ``identifier`` that is guaranteed to be unused."
        i = "Request{0}".format(IdentifiedMessage.id)
        IdentifiedMessage.id += 1
        return i

ClientHello = Message("ClientHello", [("Name", "Epoxy"), 
                                      ("ExpectedVersion", "2.0")])

