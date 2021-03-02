""" A custom binary JSON encoder for the Niagara ROP, loosely based on py-ubjson. """

import collections
import io
import struct

# Py3 support
try:
    basestring
    from collections import Mapping, Iterable
except NameError:
    basestring = str
    long = int
    from collections.abc import Mapping, Iterable


MAX_UINT8 = 2 ** 8 - 1
MAX_UINT16 = 2 ** 16 - 1
MAX_UINT32 = 2 ** 32 - 1
MIN_INT8 = -2 ** 7
MAX_INT8 = 2 ** 7 - 1
MIN_INT16 = -2 ** 15
MAX_INT16 = 2 ** 15 - 1
MIN_INT32 = -2 ** 31
MAX_INT32 = 2 ** 31 - 1


class Markers(object):
    """ Type markers as used by the struct module for writing out data in the specified type. Also
    used to indicate the size type of a string.
    
    """
    # Marker definitions: used to denote the start of objects, arrays and special types
    OBJECT_START = b'{'
    OBJECT_END = b'}'
    ARRAY_START = b'['
    ARRAY_END = b']'
    # Size types used for strings, a string is written as [SIZE_TYPE_MARKER][SIZE][UTF-8 ENCODED BYTES]
    TYPE_CHAR = b'c'
    TYPE_INT8 = b'b'
    TYPE_UINT8 = b'B'
    TYPE_BOOL = b'?'
    TYPE_INT16 = b'h'
    TYPE_UINT16 = b'H'
    TYPE_INT32 = b'l'
    TYPE_UINT32 = b'L'
    TYPE_INT64 = b'q'
    TYPE_UINT64 = b'Q'
    TYPE_FLOAT32 = b'f'
    TYPE_FLOAT64 = b'd'
    TYPE_STRING = b's'

    @classmethod
    def get_type_menu(cls):
        """ Get a menu for use in Houdini for the TYPE_ markers. """
        menu = []
        for name, value in sorted(cls.__dict__.items(), key=lambda i: i[0]):
            if name and name.startswith('TYPE_'):
                menu.append(value)
                menu.append(name[5:].lower().capitalize())
        return menu


class NiagaraData(object):
    """ Wrapper object for writing out point cache data for import in Niagara. """
    class Header(object):
        """ Wrapper object for the header of the file. """
        # The version of the file format
        version = "1.0"
        # The data type for the version field: string
        _type_version = Markers.TYPE_STRING
        # The data type for the num_samples field: uint32
        _type_num_samples = Markers.TYPE_UINT32
        # The data type for the num_frames field: uint32
        _type_num_frames = Markers.TYPE_UINT32
        # The data type for the num_points field: uint32
        _type_num_points = Markers.TYPE_UINT32
        # The data type for the num_attrib field: uint16
        _type_num_attrib = Markers.TYPE_UINT16
        # The data type for the attrib_name field: array of strings
        _type_attrib_name = Markers.TYPE_STRING
        # The data type for the attrib_size field: array of uint8
        _type_attrib_size = Markers.TYPE_UINT8
        # The data type for the attrib_data field: array of unsigned chars
        _type_attrib_data_type = Markers.TYPE_CHAR
        # The data type for the data_type field: array of strings
        _type_data_type = Markers.TYPE_STRING

        def __init__(self, *args, **kwargs):
            self.num_samples = kwargs.get('num_samples', None)
            self.num_frames = kwargs.get('num_frames', None)
            self.num_points = kwargs.get('num_points', None)
            self.num_attrib = kwargs.get('num_attrib', None)
            self.attrib_name = kwargs.get('attrib_name', None)
            self.attrib_size = kwargs.get('attrib_size', None)
            self.attrib_data_type = kwargs.get('attrib_data_type', None)
            self.data_type = kwargs.get('data_type', None)

        def to_dict(self):
            """ Returns an ordered dictionary of the header fields. """
            return collections.OrderedDict((
                ('version', self.version),
                ('num_samples', self.num_samples),
                ('num_frames', self.num_frames),
                ('num_points', self.num_points),
                ('num_attrib', self.num_attrib),
                ('attrib_name', self.attrib_name),
                ('attrib_size', self.attrib_size),
                ('attrib_data_type', self.attrib_data_type),
                ('data_type', self.data_type),
            ))
        
        def dump(self, f):
            """ Write the header in binary format to the file-like object ``f``. """
            f.write(Markers.OBJECT_START)

            write_string(f, 'version')
            write_string(f, self.version)

            write_string(f, 'num_samples')
            write_basic_value(f, self.num_samples, self._type_num_samples)

            write_string(f, 'num_frames')
            write_basic_value(f, self.num_frames, self._type_num_frames)

            write_string(f, 'num_points')
            write_basic_value(f, self.num_points, self._type_num_points)

            write_string(f, 'num_attrib')
            write_basic_value(f, self.num_attrib, self._type_num_attrib)

            write_string(f, 'attrib_name')
            write_array(f, self.attrib_name)

            write_string(f, 'attrib_size')
            write_array(f, self.attrib_size, self._type_attrib_size)

            write_string(f, 'attrib_data_type')
            write_array(f, self.attrib_data_type, self._type_attrib_data_type)

            write_string(f, 'data_type')
            write_string(f, self.data_type)

            f.write(Markers.OBJECT_END)

        def dumpb(self):
            """ Return a byte array of the header in binary format. """
            with BytesIO() as f:
                self.dump(f)
                return f.getvalue()
    
    class FrameEntry(object):
        """ A object containing the data of frame entry. """
        # The data type of the number field: uint32
        _type_number = Markers.TYPE_UINT32
        # The data type of the time field: float32
        _type_time = Markers.TYPE_FLOAT32
        # The data type for the num_points field: uint32
        _type_num_points = Markers.TYPE_UINT32

        def __init__(self, *args, **kwargs):
            self._header = kwargs.get('header', None)  # header: we need to get the attribute data types when writing the binary format
            self.number = kwargs.get('number', None)
            self.time = kwargs.get('time', None)
            # Array of points where each entry is an array of attribute values for that point
            self._frame_data = kwargs.get('frame_data', None)
            self.num_points = 0

        @property
        def header(self):
            return self._header

        @header.setter
        def header(self, in_header):
            self._header = in_header

        @property
        def frame_data(self):
            return self._frame_data
        
        @frame_data.setter
        def frame_data(self, value):
            self._frame_data = value

        def to_dict(self):
            """ Returns an ordered dict of frame entry data:
                - number: the frame number
                - time: the frame time in seconds
                - num_points: the number of points in this frame
                - frame_data: array of point attribute value arrays
            """
            return collections.OrderedDict((
                ('number', self.number),
                ('time', self.time),
                ('num_points', self.num_points),
                ('frame_data', self.frame_data),
            ))

        def dump_begin(self, f):
            """ Write this frame entry up to just before the first value in ``frame_data``, to 
                the custom binary format using the file-like object ``f``. 
                
            """
            f.write(Markers.OBJECT_START)

            write_string(f, 'number')
            write_value(f, self.number, self._type_number)

            write_string(f, 'time')
            write_value(f, self.time, self._type_time)

            write_string(f, 'num_points')
            write_value(f, self.num_points, self._type_num_points)

            write_string(f, 'frame_data')
            attrib_data_types = self._header.attrib_data_type
            f.write(Markers.ARRAY_START)

        def dump_end(self, f):
            """ Write the end markers for the frame_data array and frame_entry object to ``f``. """
            f.write(Markers.ARRAY_END)

            f.write(Markers.OBJECT_END)            

        def dump_frames(self, f, clamp_values_to_pack_type=True):
            """ Dump the content of the ``frame_data`` array to ``f``.

            Raises an IndexError if there are less points than ``num_points`` in ``frame_data``.

            """
            num_points_written = 0
            for sample in self.frame_data:
                write_array(f, sample, attrib_data_types, clamp_values_to_pack_type)
                num_points_written += 1
                # Write 'num_points'
                if num_points_written >= self.num_points:
                    break
            if num_points_written != self.num_points:
                raise IndexError(
                    '[FrameEntry] number={0:2f}, wrote less points in frame than specified in `num_points` {1} vs {2}'.format(
                        self.number, self.num_points, len(self.frame_data))
                )

        def dump(self, f, clamp_values_to_pack_type=True):
            """ Write the frame entry to the custom binary format via the file-like ``f``. """
            self.dump_begin(f)

            self.dump_frames(f, clamp_values_to_pack_type)            
            
            self.dump_end(f)

        def dumpb(self, clamp_values_to_pack_type=True):
            """ Returns a byte-array containing the frame entry in the custom binary format. """
            with BytesIO() as f:
                self.dump(f, clamp_values_to_pack_type)
                return f.getvalue()

    def __init__(self, *args, **kwargs):
        self._header = NiagaraData.Header()
        # Array of FrameEntry instances
        self._frames = []

    @property
    def header(self):
        return self._header
    
    def add_frame(self, frame_entry):
        """ Add a ``frame_entry``. ``frame_entry`` must be an instance of ``NiagaraData.FrameEntry``. """
        if not isinstance(frame_entry, NiagaraData.FrameEntry):
            raise TypeError('Expected NiagaraData.FrameEntry not {}'.format(type(frame_entry)))
        frame_entry.header = self.header
        self._frames.append(frame_entry)

    def _gen_frame_dict_entries(self):
        """ Returns a generator of ordered dicts, one for each FrameEntry in ``self._frames``. Calls
        :meth:`NiagaraData.FrameEntry.to_dict()` to get the dictionary for each FrameEntry.
        
        """
        for frame in self._frames:
            yield frame.to_dict()

    def to_dict(self):
        """ Returns an ordered dict of point cache:
            - header: ``NiagaraData.Header`` as a dict via its to_dict function
            - cache_data:
                - frames: list of ``NiagaraData.FrameEntry`` instances as dict via the to_dict function.
        """
        frames = self._gen_frame_dict_entries()
        return collections.OrderedDict((
            ('header', self.header.to_dict()),
            ('cache_data', collections.OrderedDict((
                ('frames', list(frames)),
            ))),
        ))

    def dump_begin(self, f):
        """ Begin writing the point cache in custom binary format to ``f``. Writes up the beginning of the ``cache_data.frames`` array. """
        f.write(Markers.OBJECT_START)
        write_string(f, 'header')
        self.header.dump(f)
        write_string(f, 'cache_data')
        f.write(Markers.OBJECT_START)
        write_string(f, 'frames')
        f.write(Markers.ARRAY_START)

    def dump_end(self, f):
        """ Writes from the end of the ``cache_data.frames`` array to the end of the cache to ``f``. """
        f.write(Markers.ARRAY_END)
        f.write(Markers.OBJECT_END)
        f.write(Markers.OBJECT_END)

    def dump(self, f, clamp_values_to_pack_type=True):
        """ Writes the point cache in custom binary format to ``f``. """
        self.dump_begin(f)
        for frame_entry in self._frames:
            frame_entry.dump(f, clamp_values_to_pack_type)
        self.dump_end(f)

    def dumpb(self, clamp_values_to_pack_type=True):
        """ Returns a bytes array of the point cache in custom binary format. """
        with BytesIO() as f:
            self.dump(f, clamp_values_to_pack_type)
            return f.getvalue()


def write_string(f, value):
    """ Write a string to our custom binary format. Strings are all utf-8 encoded.
    For a string we write three pieces of information to ``f``:
        - string size type marker: one of ``Markers.TYPE_``
        - the size of the string in bytes, packed according to the size type marker
        - the string byte array itself packed as chars
    
    Raises a ``ValueError`` if the string's size is greater than can be represented with uint32.

    """
    if hasattr(value, 'encode'):
        # Encode to utf-8 
        encoded_byte_string = value.encode('utf-8')
    else:
        # Assuming here that this is already a utf-8 bytes array
        encoded_byte_string = value
    # Write the size type marker, first determine the length
    # of the string and check 
    num_bytes = len(encoded_byte_string)
    size_type = None
    if num_bytes <= MAX_UINT8:
        size_type = Markers.TYPE_UINT8
    elif num_bytes <= MAX_UINT16:
        size_type = Markers.TYPE_UINT16
    elif num_bytes <= MAX_UINT32:
        size_type = Markers.TYPE_UINT32
    else:
        raise ValueError('String too long to encode.')
    f.write(size_type)
    write_basic_value(f, num_bytes, size_type)
    f.write(encoded_byte_string)


def write_basic_value(f, value, pack_type=None, clamp=True):
    """ Write a plain old data ``value``, such as float, int or bool, to ``f``, packed according
    to ``pack_type``.

    Casts ``value`` to the appropriate type depending on ``pack_type``. 

    Multi-byte values are written with little-endian encoding.

    If ``clamp`` is True, then values that are outside of the min/max of ``pack_type`` are clamped.
    If ``False``, ``struct.pack`` will raise a ``struct.error``.

    """
    casted_value = None
    if pack_type == Markers.TYPE_BOOL:
        casted_value = bool(value)
    elif pack_type == Markers.TYPE_CHAR:
        if isinstance(value, bytes):
            casted_value = value
        elif isinstance(value, basestring):
            casted_value = value.encode('utf-8')
        else:
            casted_value = str(value).encode('utf-8')
        if casted_value:
            # Slice to get a bytes array of length 1 in both py2.7 and py3
            casted_value = casted_value[0:1]
        else:
            casted_value = b'\0'
    elif (pack_type == Markers.TYPE_INT8 or pack_type == Markers.TYPE_UINT8 or 
            pack_type == Markers.TYPE_INT16 or pack_type == Markers.TYPE_UINT16 or 
            pack_type == Markers.TYPE_INT32 or pack_type == Markers.TYPE_UINT32 or 
            pack_type == Markers.TYPE_INT64 or pack_type == Markers.TYPE_UINT64):
        casted_value = int(value)
    elif pack_type == Markers.TYPE_FLOAT32 or pack_type == Markers.TYPE_FLOAT64:
        casted_value = float(value)
    else:
        casted_value = value

    # Optionally clamp values that are outside of the pack_type range (if clamp is False
    # and a value is out of range, struct.pack will raise a struct.error)
    if clamp:
        if pack_type == Markers.TYPE_INT8:
            if casted_value < MIN_INT8:
                casted_value = MIN_INT8
            elif casted_value > MAX_INT8:
                casted_value = MAX_INT8
        elif pack_type == Markers.TYPE_UINT8:
            if casted_value < 0:
                casted_value = 0
            elif casted_value > MAX_UINT8:
                casted_value = MAX_UINT8
        elif pack_type == Markers.TYPE_INT16:
            if casted_value < MIN_INT16:
                casted_value = MIN_INT16
            elif casted_value > MAX_INT16:
                casted_value = MAX_INT16
        elif pack_type == Markers.TYPE_UINT16:
            if casted_value < 0:
                casted_value = 0
            elif casted_value > MAX_UINT16:
                casted_value = MAX_UINT16
        elif pack_type == Markers.TYPE_INT32:
            if casted_value < MIN_INT32:
                casted_value = MIN_INT32
            elif casted_value > MAX_INT32:
                casted_value = MAX_INT32
        elif pack_type == Markers.TYPE_UINT32:
            if casted_value < 0:
                casted_value = 0
            elif casted_value > MAX_UINT32:
                casted_value = MAX_UINT32
        # If a casted_value is outside of 64 range, always range an exception
    f.write(struct.pack('<{0}'.format(pack_type.decode('utf-8')), casted_value))


def write_object(f, obj, pack_type=None, clamp=True):
    """ Write a ``Mapping`` like object to ``f`` in our custom binary format.

    ``Markers.OBJECT_START`` is written first, then each field-value pair is
    written, first the field name as a string via ``write_string`` and then
    the value via ``write_value``.

    ``pack_type`` defaults to ``None``. If ``pack_type`` is one of ``Markers.TYPE_*``,
    then this type is used as the pack_type for each value in ``obj``. If ``pack_type``
    is a mapping, then it is expected to have a keys matching each ``field`` in ``obj``,
    and each key should map to the appropriate pack type for that value.

    If ``clamp`` is True, then values that are outside of the min/max of ``pack_type`` are clamped.
    If ``False``, ``struct.pack`` will raise a ``struct.error``.

    """
    f.write(Markers.OBJECT_START)
    pack_type_is_mapping = bool(isinstance(pack_type, Mapping))
    for key, value in obj.items():
        if not isinstance(key, basestring):
            raise TypeError('Mapping keys must be strings: {0}'.format(key))
        write_string(f, key)
        if pack_type_is_mapping:
            write_value(f, value, pack_type.get(key), clamp)
        else:
            write_value(f, value, pack_type, clamp)
    f.write(Markers.OBJECT_END)


def open_array(f):
    """ Write ``Markers.ARRAY_START``, to indicate the start of an array, to ``f``. """
    f.write(Markers.ARRAY_START)


def close_array(f):
    """ Write ``Markers.ARRAY_START``, to indicate the end of an array, to ``f``. """
    f.write(Markers.ARRAY_END)


def write_array(f, obj, pack_type=None, clamp=True):
    """ Writes ``obj``, a sequence, as an array of values to ``f``. 
    
    ``pack_type`` defaults to ``None``. If not ``None`` it can be used to specify a single pack type to
    use for all values in the array, or it can be a sequence, with the same length as ``obj``, of pack types.

    If ``clamp`` is True, then values that are outside of the min/max of ``pack_type`` are clamped.
    If ``False``, ``struct.pack`` will raise a ``struct.error``.

    """
    open_array(f)
    if obj:
        if pack_type and not isinstance(pack_type, bytes) and isinstance(pack_type, Iterable):
            index = 0
            for value in obj:
                write_value(f, value, pack_type[index], clamp)
                index += 1
        else:
            for value in obj:
                write_value(f, value, pack_type, clamp)
    close_array(f)


def write_value(f, value, pack_type=None, clamp=True):
    """ Generic function for wriiting a ``value`` to ``f`` with a specified (optional) ``pack_type``.

    Supports:
    
        - ``Mapping`` types via ``write_object
        - strings via ``write_string``
        - ``Iterable`` types via ``write_array``
        - plain old types, int, float, bool, None, via ``write_basic_value``

    ``pack_type`` can be a single value, ``Mapping`` or ``Iterable``, depending on the type of ``value``. See
    the various ``write_`` functions for the different uses.

    If ``clamp`` is True, then values that are outside of the min/max of ``pack_type`` are clamped.
    If ``False``, ``struct.pack`` will raise a ``struct.error``.

    Raises:
        ``ValueError``: If the type of ``value`` is not supported.
        
    """
    if isinstance(value, Mapping):
        write_object(f, value, pack_type, clamp)
    elif isinstance(value, (bytes, basestring)):
        if pack_type == Markers.TYPE_CHAR:
            # Slice value to ensure we don't get an int in python 3 if value is
            # bytes
            write_basic_value(f, value[0:1] if value else 0, pack_type, clamp)
        else:
            write_string(f, value)
    elif isinstance(value, Iterable):
        write_array(f, value, pack_type, clamp)
    elif isinstance(value, (int, float, bool, None)):
        write_basic_value(f, value, pack_type, clamp)
    else:
        raise TypeError('Unsupported type for {0}'.format(value))
