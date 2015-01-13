# http://stackoverflow.com/questions/27929895/pretty-print-and-substitute-numpy-arrays/27932325#27932325

#  Small modification of pprint, to print resumedly numpy.ndarray objects
#  Original author of pprint:   Fred L. Drake, Jr.
#                               fdrake@acm.org
#
#  This is a simple little module I wrote to make life easier.  I didn't
#  see anything quite like it in the library, though I may have overlooked
#  something.  I wrote this when I was trying to read some heavily nested
#  tuples with fairly non-descriptive content.  This is modeled very much
#  after Lisp/Scheme - style pretty-printing of lists.  If you find it
#  useful, thank small children who sleep at night.
 
"""Support to pretty-print lists, tuples, & dictionaries recursively.
 
Very simple, but useful, especially in debugging data structures.
 
Classes
-------
 
PrettyPrinter()
   Handle pretty-printing operations onto a stream using a configured
   set of formatting parameters.
 
Functions
---------
 
pformat()
   Format a Python object into a pretty-printed representation.
 
pprint()
   Pretty-print a Python object to a stream [default is sys.stdout].
 
saferepr()
   Generate a 'standard' repr()-like value, but protect against recursive
   data structures.
 
"""
 
import sys as _sys
import warnings
try:
    from numpy import ndarray
    np_arrays = True
except ImportError:
    np_arrays = False
 
try:
    from cStringIO import StringIO as _StringIO
except ImportError:
    from StringIO import StringIO as _StringIO
 
__all__ = ["pprint","pformat","isreadable","isrecursive","saferepr",
           "PrettyPrinter"]
 
# cache these for faster access:
_commajoin = ", ".join
_id = id
_len = len
_type = type
 
 
def pprint(object, stream=None, indent=1, width=80, depth=None):
    """Pretty-print a Python object to a stream [default is sys.stdout]."""
    printer = PrettyPrinter(
        stream=stream, indent=indent, width=width, depth=depth)
    printer.pprint(object)
 
def pformat(object, indent=1, width=80, depth=None):
    """Format a Python object into a pretty-printed representation."""
    return PrettyPrinter(indent=indent, width=width, depth=depth).pformat(object)
 
def saferepr(object):
    """Version of repr() which can handle recursive data structures."""
    return _safe_repr(object, {}, None, 0)[0]
 
def isreadable(object):
    """Determine if saferepr(object) is readable by eval()."""
    return _safe_repr(object, {}, None, 0)[1]
 
def isrecursive(object):
    """Determine if object requires a recursive representation."""
    return _safe_repr(object, {}, None, 0)[2]
 
def _sorted(iterable):
    with warnings.catch_warnings():
        if _sys.py3kwarning:
            warnings.filterwarnings("ignore", "comparing unequal types "
                                    "not supported", DeprecationWarning)
        return sorted(iterable)
 
class PrettyPrinter:
    def __init__(self, indent=1, width=80, depth=None, stream=None):
        """Handle pretty printing operations onto a stream using a set of
       configured parameters.
 
       indent
           Number of spaces to indent for each level of nesting.
 
       width
           Attempted maximum number of columns in the output.
 
       depth
           The maximum depth to print out nested structures.
 
       stream
           The desired output stream.  If omitted (or false), the standard
           output stream available at construction will be used.
 
       """
        indent = int(indent)
        width = int(width)
        assert indent >= 0, "indent must be >= 0"
        assert depth is None or depth > 0, "depth must be > 0"
        assert width, "width must be != 0"
        self._depth = depth
        self._indent_per_level = indent
        self._width = width
        if stream is not None:
            self._stream = stream
        else:
            self._stream = _sys.stdout
 
    def pprint(self, object):
        self._format(object, self._stream, 0, 0, {}, 0)
        self._stream.write("\n")
 
    def pformat(self, object):
        sio = _StringIO()
        self._format(object, sio, 0, 0, {}, 0)
        return sio.getvalue()
 
    def isrecursive(self, object):
        return self.format(object, {}, 0, 0)[2]
 
    def isreadable(self, object):
        s, readable, recursive = self.format(object, {}, 0, 0)
        return readable and not recursive
  
    def _repr(self, object, context, level):
        repr, readable, recursive = self.format(object, context.copy(),
                                                self._depth, level)
        if not readable:
            self._readable = False
        if recursive:
            self._recursive = True
        return repr
 
    def format(self, object, context, maxlevels, level):
        """Format object for a specific context, returning a string
       and flags indicating whether the representation is 'readable'
       and whether the object represents a recursive construct.
       """
        return _safe_repr(object, context, maxlevels, level)
 
 
# Return triple (repr_string, isreadable, isrecursive).
 
def _safe_repr(object, context, maxlevels, level):
    typ = _type(object)
    if typ is str:
        if 'locale' not in _sys.modules:
            return repr(object), True, False
        if "'" in object and '"' not in object:
            closure = '"'
            quotes = {'"': '\\"'}
        else:
            closure = "'"
            quotes = {"'": "\\'"}
        qget = quotes.get
        sio = _StringIO()
        write = sio.write
        for char in object:
            if char.isalpha():
                write(char)
            else:
                write(qget(char, repr(char)[1:-1]))
        return ("%s%s%s" % (closure, sio.getvalue(), closure)), True, False
 
    r = getattr(typ, "__repr__", None)
    if issubclass(typ, dict) and r is dict.__repr__:
        if not object:
            return "{}", True, False
        objid = _id(object)
        if maxlevels and level >= maxlevels:
            return "{...}", False, objid in context
        if objid in context:
            return _recursion(object), False, True
        context[objid] = 1
        readable = True
        recursive = False
        components = []
        append = components.append
        level += 1
        saferepr = _safe_repr
        for k, v in _sorted(object.items()):
            krepr, kreadable, krecur = saferepr(k, context, maxlevels, level)
            vrepr, vreadable, vrecur = saferepr(v, context, maxlevels, level)
            append("%s: %s" % (krepr, vrepr))
            readable = readable and kreadable and vreadable
            if krecur or vrecur:
                recursive = True
        del context[objid]
        return "{%s}" % _commajoin(components), readable, recursive
 
    if (issubclass(typ, list) and r is list.__repr__) or \
       (issubclass(typ, tuple) and r is tuple.__repr__):
        if issubclass(typ, list):
            if not object:
                return "[]", True, False
            format = "[%s]"
        elif _len(object) == 1:
            format = "(%s,)"
        else:
            if not object:
                return "()", True, False
            format = "(%s)"
        objid = _id(object)
        if maxlevels and level >= maxlevels:
            return format % "...", False, objid in context
        if objid in context:
            return _recursion(object), False, True
        context[objid] = 1
        readable = True
        recursive = False
        components = []
        append = components.append
        level += 1
        for o in object:
            orepr, oreadable, orecur = _safe_repr(o, context, maxlevels, level)
            append(orepr)
            if not oreadable:
                readable = False
            if orecur:
                recursive = True
        del context[objid]
        return format % _commajoin(components), readable, recursive
 
    rep = repr(object)
    return rep, (rep and not rep.startswith('<')), False
 
 
def _recursion(object):
    return ("<Recursion on %s with id=%s>"
            % (_type(object).__name__, _id(object)))
 
if __name__ == "__main__":
    import numpy as np
    x = {'foo': {'bar':np.linspace(0,5)}}
    print x
    pprint(x)