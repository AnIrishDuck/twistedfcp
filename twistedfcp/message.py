"""
Defines messages sent through the Freenet Client Protocol.

"""

class Message(object):
    "A simple message with a name and arguments."

    def __getitem__(self, el):
        for k, v in self.args:
            if k == el: return v

        raise KeyError("The key {0} is not in the message.".format(el))

    def __contains__(self, el):
        return any(k == el for k, _ in self.args)

    def __init__(self, name, args):
        self.name = name
        self.args = args

class IdentifiedMessage(Message):
    "A message with an ``Identifier`` that is used to identify sessions."
    current_id = 0
    def __init__(self, *args):
        Message.__init__(self, *args)
        self.args.append(["Identifier", self.unused_identifier])

    @property
    def id(self): return self["Identifier"]

    @property
    def unused_identifier(self):
        "Returns an ``identifier`` that is guaranteed to be unused."
        i = "Request{0}".format(IdentifiedMessage.current_id)
        IdentifiedMessage.current_id += 1
        return i

ClientHello = Message("ClientHello", [("Name", "Epoxy"), 
                                      ("ExpectedVersion", "2.0")])

