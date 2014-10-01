"""
This is Victor Stinner's pure-Python implementation of PEP 383: the "surrogateescape" error
handler of Python 3.

Source: misc/python/surrogateescape.py in https://bitbucket.org/haypo/misc
"""

# This code is released under the Python license and the BSD 2-clause license

import codecs
import sys

from path import PY2, PY3, bytes_type

FS_ERRORS = 'surrogateescape'
# normalize the filesystem encoding name.
# For example, we expect "utf-8", not "UTF8".
FS_ENCODING = codecs.lookup(sys.getfilesystemencoding()).name


# -- Python 2/3 compatibility -------------------------------------
b = lambda x: x.encode('latin1')
_unichr = chr
bytes_chr = lambda code: bytes_type((code,))

if PY2:
    b = lambda x: x
    _unichr = unichr
    bytes_chr = chr
# -- Python 2/3 compatibility -------------------------------------


def surrogateescape(exc):
    """
    Pure Python implementation of the PEP 383: the "surrogateescape" error
    handler of Python 3.
    """
    if isinstance(exc, UnicodeDecodeError):
        decoded = []
        for ch in exc.object[exc.start:exc.end]:
            if PY3:
                code = ch
            else:
                code = ord(ch)
            if 0x80 <= code <= 0xFF:
                decoded.append(_unichr(0xDC00 + code))
            elif code <= 0x7F:
                decoded.append(_unichr(code))
            else:
                raise exc
        decoded = str().join(decoded)
        return (decoded, exc.end)
    else:
        print(exc.args)
        ch = exc.object[exc.start:exc.end]
        code = ord(ch)
        if not 0xDC80 <= code <= 0xDCFF:
            raise exc
        print(exc.start)
        byte = _unichr(code - 0xDC00)
        print(repr(byte))
        return (byte, exc.end)


if PY2:
    codecs.register_error(FS_ERRORS, surrogateescape)


def encodefilename(fn):
    if FS_ENCODING == 'ascii':
        # ASCII encoder of Python 2 expects that the error handler returns a
        # Unicode string encodable to ASCII, whereas our surrogateescape error
        # handler has to return bytes in 0x80-0xFF range.
        encoded = []
        for index, ch in enumerate(fn):
            code = ord(ch)
            if code < 128:
                ch = bytes_chr(code)
            elif 0xDC80 <= code <= 0xDCFF:
                ch = bytes_chr(code - 0xDC00)
            else:
                raise UnicodeEncodeError(FS_ENCODING,
                    fn, index, index+1,
                    'ordinal not in range(128)')
            encoded.append(ch)
        return ''.join(encoded)
    elif FS_ENCODING == 'utf-8':
        # UTF-8 encoder of Python 2 encodes surrogates, so U+DC80-U+DCFF
        # doesn't go through our error handler
        encoded = []
        for index, ch in enumerate(fn):
            code = ord(ch)
            if 0xD800 <= code <= 0xDFFF:
                if 0xDC80 <= code <= 0xDCFF:
                    ch = bytes_chr(code - 0xDC00)
                    encoded.append(ch)
                else:
                    raise UnicodeEncodeError(
                        FS_ENCODING,
                        fn, index, index+1, 'surrogates not allowed')
            else:
                ch_utf8 = ch.encode('utf-8')
                encoded.append(ch_utf8)
        return bytes_type().join(encoded)
    else:
        return fn.encode(FS_ENCODING, FS_ERRORS)


def decodefilename(fn):
    return fn.decode(FS_ENCODING, FS_ERRORS)
