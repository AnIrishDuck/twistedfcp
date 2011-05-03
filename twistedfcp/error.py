"Defines errors that can be thrown by the Freenet Node."

fetch_error_codes = {
    1:	 "(Depreciated) Too many levels of archive recursion",
    2:	 "(Depreciated) Unknown splitfile metadata",
    3:   "Unknown metadata",
    4:	 "Invalid metadata",
    5:	 "Archive failure",
    6:	 "Block decode error",
    7:	 "(Depreciated) Too many metadata levels",
    8:	 "Too many archive restarts",
    9:	 "Too many levels of recursion",
    10:	 "Tried to access an archive file but not in an archive " +
         "(this isn't an archive, but you seem to be telling me it is)",
    11:	 "The URI has more metastrings and I can't deal with them",
    12:	 "Bucket error (ie. internal, ie. not your fault!)",
    13:	 "Data not found (I've looked, and it's really not there. Get over it)",
    14:	 "Route not found (I can't get to where it would be)",
    15:	 "Rejected overload (A downstream node was too busy to deal with us " +
         "right now)",
    16:	 "(Depreciated) Too many redirects",
    17:	 "Internal error",
    18:	 "Transfer failed (I found it, but never managed to get the data)",
    19:	 "Splitfile error",
    20:	 "Invalid URI",
    21:	 "Too big!",
    22:	 "Metadata is too big",
    23:	 "Too many blocks per segment (in a splitfile)",
    24:	 "Not enough metastrings " + 
         "(be more specific - put /something at the end)",
    25:	 "Cancelled",
    26:	 "Archive restart",
    27:	 "Permanent redirect "
         "(there's a newer version of the USK you asked for)",
    28:	 "All data not found (means we fetched some data but not all - " + 
         "perhaps a redirect to a file that hasn't been inserted)",
    29:	 "Requestor specified a list of allowed MIME types, and " + 
         "the key's type wasn't in the list",
    30:	 "A node killed the request " + 
         "because it had recently been tried and had DNFed"}

class FetchFailed(Exception):
    def __init__(self, code):
        self.code = code
        Exception.__init__("Get failed with code {code}. {msg}".format(
            msg=fetch_error_codes[code], code=code))
