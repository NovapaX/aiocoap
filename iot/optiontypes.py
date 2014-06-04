# This file is part of the txThings project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# txThings is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

import abc
import collections
import struct

class OptionType(metaclass=abc.ABCMeta):
    """Interface for decoding and encoding option values

    Instances of `OptionType`s are collected in a list in a Message.opt Options
    object, and provide a translation between the CoAP octet-stream (accessed
    using the `encode()`/`decode()` method pair) and the interpreted value
    (accessed via the `value` attribute).

    Note that OptionType objects usually don't need to be handled by library
    users; the recommended way to read and set options is via the Options
    object'sproperties (eg. `message.opt.uri_path = ('.well-known',
    'core')`)."""

    @abc.abstractmethod
    def __init__(self, number, value):
        self.name = name
        self.value = value

    @abc.abstractmethod
    def encode(self):
        """Return the option's value in serialzied form"""

    @abc.abstractmethod
    def decode(self, rawdata):
        """Set the option's value from the bytes in rawdata"""

    @property
    def length(self):
        """Indicate the length of the encoded value"""

        return len(self.encode())

class StringOption(OptionType):
    """String CoAP option - used to represent string options."""

    def __init__(self, number, value=""):
        self.value = value
        self.number = number

    def encode(self):
        # FIXME: actually, this should be utf8 of the net-unicode form (maybe it is)
        rawdata = self.value.encode('utf-8')
        return rawdata

    def decode(self, rawdata):
        self.value = rawdata.decode('utf-8')

    def _length(self):
        return len(self.value.encode('utf-8'))
    length = property(_length)

class OpaqueOption(OptionType):
    """Opaque CoAP option - used to represent opaque options."""

    def __init__(self, number, value=b""):
        self.value = value
        self.number = number

    def encode(self):
        rawdata = self.value
        return rawdata

    def decode(self, rawdata):
        self.value = rawdata  # if rawdata is not None else ""

    def _length(self):
        return len(self.value)
    length = property(_length)


class UintOption(OptionType):
    """Uint CoAP option - used to represent uint options."""

    def __init__(self, number, value=0):
        self.value = value
        self.number = number

    def encode(self):
        rawdata = struct.pack("!L", self.value)  # For Python >3.1 replace with int.to_bytes()
        return rawdata.lstrip(bytes([0]))

    def decode(self, rawdata):  # For Python >3.1 replace with int.from_bytes()
        value = 0
        for byte in rawdata:
            value = (value * 256) + byte
        self.value = value
        return self

    def _length(self):
        if self.value > 0:
            return (self.value.bit_length() - 1) // 8 + 1
        else:
            return 0
    length = property(_length)


class BlockOption(OptionType):
    """Block CoAP option - special option used only for Block1 and Block2 options.
       Currently it is the only type of CoAP options that has
       internal structure."""
    BlockwiseTuple = collections.namedtuple('BlockwiseTuple', ['block_number', 'more', 'size_exponent'])

    def __init__(self, number, value=(0, None, 0)):
        self.value = self.BlockwiseTuple._make(value)
        self.number = number

    def encode(self):
        as_integer = (self.value[0] << 4) + (self.value[1] * 0x08) + self.value[2]
        rawdata = struct.pack("!L", as_integer)  # For Python >3.1 replace with int.to_bytes()
        return rawdata.lstrip(bytes([0]))

    def decode(self, rawdata):
        as_integer = 0
        for byte in rawdata:
            as_integer = (as_integer * 256) + byte
        self.value = self.BlockwiseTuple(block_number=(as_integer >> 4), more=bool(as_integer & 0x08), size_exponent=(as_integer & 0x07))

    def _length(self):
        return ((self.value[0].bit_length() + 3) // 8 + 1)
    length = property(_length)