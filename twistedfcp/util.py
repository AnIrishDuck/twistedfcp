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

