
class Message(object):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class IdentifiedMessage(Message):
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
        i = "Request{0}".format(IdentifiedMessage.id)
        IdentifiedMessage.id += 1
        return i

ClientHello = Message("ClientHello", [("Name", "Epoxy"), 
                                      ("ExpectedVersion", "2.0")])

