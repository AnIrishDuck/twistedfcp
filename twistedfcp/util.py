"""
Defines utility functions for the ``twistedfcp`` module.

"""

def sequence(f):
    """
    Sequences a generator function through deferreds. Takes each sent 
    ``Deferred`` and attaches a callback to it that sends the generator
    function the results when they arrive. Continues to recursively do this
    until the generator function is exhausted.

    """
    def _inner(*args):
        gen = f(*args)
        first = gen.next()
        def cb(*args):
            if len(args) == 1: args = args[0]
            try:
                d = gen.send(args)
                return d.addCallback(cb)
            except StopIteration:
                pass
    
        return first.addCallback(cb)
    
    return _inner

