
# Python to PAN

def pan(obj, indent=0):
    """pan(OBJ) -- return a string representing OBJ in the PAN language"""

    spaces = "  " * (indent + 1)
    accumulator = list()
    if isinstance(obj, dict):
        accumulator.append("nlist(")
        for key in obj:
            val = pan(obj[key], indent + 1)
            accumulator.append("%s'%s', %s," % (spaces, key, val))
        # remove the last comma
        accumulator[-1] = accumulator[-1].rstrip(",")
        accumulator.append("%s)" % ("  " * indent))

    elif isinstance(obj, list):
        accumulator.append("list(")
        for item in obj:
            val = pan(item, indent + 1)
            accumulator.append("%s%s," % (spaces, val))
        # remove the last comma
        accumulator[-1] = accumulator[-1].rstrip(",")
        accumulator.append("%s)" % ("  " * indent))

    elif isinstance(obj, basestring):
        quote = '"'
        if '"' in obj:
            quote = "'"
        accumulator.append("%s%s%s" % (quote, obj, quote))

    elif isinstance(obj, int):
        accumulator.append("%d" % obj)

    else:
        accumulator.append(pan(str(obj)))

    if (len(accumulator) == 1):
        return accumulator[0]

    return "\n".join(("%s" % x) for x in accumulator)
