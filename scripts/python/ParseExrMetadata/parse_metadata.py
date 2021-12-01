#-*- coding: utf-8 -*-
import os
import sys
import subprocess
import struct

import logging

logger = logging.getLogger('vvzen.parse_metadata')


class EXR_ATTRIBUTES:
    COMPRESSION_VALUES = ('NO_COMPRESSION', 'RLE_COMPRESSION',
                          'ZIPS_COMPRESSION', 'ZIP_COMPRESSION',
                          'PIZ_COMPRESSION', 'PXR24_COMPRESSION',
                          'B44_COMPRESSION', 'B44A_COMPRESSION')

    LINE_ORDER = ('INCREASING_Y', 'DECREASING_Y', 'RANDOM_Y')

    ENVMAP_TYPES = ('ENVMAP_LATLONG', 'ENVMAP_CUBE')


def read_until_null(filebuffer, maxbytes=1024):
    """Reads a file until a null character

    Args:
        filebuffer (obj): a file that was opened with open()
        maxbytes (int): number of bytes that will be read if no null byte is found
        Avoids infinite loops.

    Returns:
        str: string concatenation of the bytes read
        int: how many bytes were read
    """

    current_string = b''
    current_byte = filebuffer.read(1)
    bytes_read = 1

    while current_byte != b'\x00':

        current_string += current_byte
        # print('current byte: {}'.format(current_byte))

        bytes_read += 1
        current_byte = struct.unpack('c', filebuffer.read(1))[0]

        if bytes_read > maxbytes:
            print('exiting due to infinite loop')
            break

    return current_string, bytes_read


def convert_to_unicode_string(data):
    """Recursively convert dictionary keys and values to unicode strings"""
    if isinstance(data, dict):
        return {
            convert_to_unicode_string(k): convert_to_unicode_string(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [convert_to_unicode_string(v) for v in data]
    elif isinstance(data, bytes):
        return str(data, encoding='utf-8')
    else:
        return data


def read_exr_header(exrpath, maxreadsize=2000):
    """Parses the header of an exr file using the official specification :
    https://www.openexr.com/documentation/openexrfilelayout.pdf

    Args:
        exrpath (str): absolute path to the exr file
        maxreadsize (int, optional): Avoids infinite loops in case a final null byte is never encountered or the exr is formatted in a bad way. Defaults to 2000.

    Raises:
        OSError: if the exr does not exist
        TypeError: if the an unknown exr attribute is encountered

    Returns:
        dict: with the metadata
    """

    if not os.path.exists(exrpath):
        raise OSError('given EXR path does not exist ({})'.format(exrpath))

    exr_file = open(exrpath, 'rb')

    metadata = {}

    try:

        magic_number = struct.unpack('i', exr_file.read(4))
        logger.info('magic_number: {}'.format(magic_number[0]))

        openxr_version_number = struct.unpack('c', exr_file.read(1))
        logger.info('OpenEXR Version Number: {}'.format(
            ord(openxr_version_number[0])))

        version_field_attrs = struct.unpack('ccc', exr_file.read(3))
        logger.info('version_field_attrs : {} {} {}'.format(
            ord(version_field_attrs[0]), ord(version_field_attrs[1]),
            ord(version_field_attrs[2])))

        i = 0

        while i < maxreadsize:

            # We'll always have attribute name, attribute type separated by a null byte
            # Then attribute size and attribute value follow
            attribute_name, attribute_name_length = read_until_null(exr_file)
            attribute_type, _ = read_until_null(exr_file)
            attribute_size = int(struct.unpack('i', exr_file.read(4))[0])

            # If we're reading only byte it means it's the null byte
            # and we've reached the end of the header
            if attribute_name_length == 1:
                logger.info('reached the end of the header!')
                break

            if not attribute_name in metadata:
                metadata[attribute_name] = {}

            # print('attribute name: {}, length: {}, type: {}, size: {}'.format(
            #     attribute_name, attribute_name_length, attribute_type,
            #     attribute_size))

            # How many bytes of the attribute value we've read
            byte_count = 0

            # Parse the attribute value

            if attribute_type == b'box2i':
                box_values = struct.unpack('i' * 4, exr_file.read(4 * 4))

                metadata[attribute_name] = {
                    'xMin': box_values[0],
                    'yMin': box_values[1],
                    'xMax': box_values[2],
                    'yMax': box_values[3]
                }

            elif attribute_type == b'box2f':
                box_values = struct.unpack('f' * 4, exr_file.read(4 * 4))

                metadata[attribute_name] = {
                    'xMin': box_values[0],
                    'yMin': box_values[1],
                    'xMax': box_values[2],
                    'yMax': box_values[3]
                }

            elif attribute_type == b'chlist':

                channel_data = {}

                while byte_count < attribute_size:

                    channel_name, channel_name_length = read_until_null(
                        exr_file)

                    byte_count += channel_name_length
                    # print('read {} bytes of {}'.format(byte_count,
                    #                                    attribute_size))

                    # If we've read only one byte it means it was a null char
                    # We've found the end of the channels attribute
                    if channel_name_length == 1:
                        break

                    pixel_type = struct.unpack('i', exr_file.read(4 * 1))[0]
                    byte_count += 4
                    p_linear = struct.unpack('B', exr_file.read(1 * 1))[0]
                    byte_count += 1
                    reserved = struct.unpack('ccc', exr_file.read(1 * 3))
                    byte_count += 3
                    x_sampling = struct.unpack('i', exr_file.read(4 * 1))[0]
                    byte_count += 4
                    y_sampling = struct.unpack('i', exr_file.read(4 * 1))[0]
                    byte_count += 4

                    channel_data[channel_name] = {
                        'pixel_type': pixel_type,
                        'pLinear': p_linear,
                        'reserved': [ord(c) for c in reserved],
                        'xSampling': x_sampling,
                        'ySampling': y_sampling
                    }

                    metadata[attribute_name] = channel_data

            elif attribute_type == b'chromaticities':
                chromaticities = struct.unpack('f' * 8, exr_file.read(4 * 8))
                metadata[attribute_name] = {
                    'redX': chromaticities[0],
                    'redY': chromaticities[1],
                    'greenX': chromaticities[2],
                    'greenY': chromaticities[3],
                    'blueX': chromaticities[4],
                    'blueY': chromaticities[5],
                    'whiteX': chromaticities[6],
                    'whiteY': chromaticities[7],
                }

            elif attribute_type == b'compression':
                compression_value = struct.unpack('B', exr_file.read(1))
                compression_value = int(compression_value[0])

                try:
                    metadata['compression'] = EXR_ATTRIBUTES.COMPRESSION_VALUES[
                        compression_value]

                except IndexError:
                    metadata['compression'] = 'unknown'

            elif attribute_type == b'double':
                attribute_value = struct.unpack('d', exr_file.read(8 * 1))
                metadata[attribute_name] = attribute_value[0]

            elif attribute_type == b'envmap':
                attribute_value = struct.unpack('B', exr_file.read(1 * 1))

                try:
                    metadata[attribute_name] = EXR_ATTRIBUTES.ENVMAP_TYPES[
                        attribute_value[0]]
                except IndexError:
                    metadata[attribute_name] = 'unknown'

            elif attribute_type == b'float':
                float_value = struct.unpack('f', exr_file.read(4))
                metadata[attribute_name] = float_value[0]

            elif attribute_type == b'int':
                attribute_value = int(
                    struct.unpack('i', exr_file.read(4 * 1))[0])

                metadata[attribute_name] = attribute_value

            elif attribute_type == b'keycode':
                attribute_values = struct.unpack('i' * 7, exr_file.read(4 * 7))

                metadata[attribute_name] = {
                    'filmMfcCode': attribute_values[0],
                    'filmType': attribute_values[1],
                    'prefix': attribute_values[2],
                    'count': attribute_values[3],
                    'perfOffset': attribute_values[4],
                    'perfsPerFrame': attribute_values[5],
                    'perfsPerCount': attribute_values[6]
                }

            elif attribute_type == b'lineOrder':
                line_order = int(struct.unpack('B', exr_file.read(1))[0])
                metadata[attribute_name] = EXR_ATTRIBUTES.LINE_ORDER[line_order]

            elif attribute_type == b'm33f':
                attribute_values = struct.unpack('f' * 9, exr_file.read(4 * 9))
                metadata[attribute_name] = attribute_values

            elif attribute_type == b'm44f':
                attribute_values = struct.unpack('f' * 16,
                                                 exr_file.read(4 * 16))
                metadata[attribute_name] = attribute_values
            
            elif attribute_type == b'm44d':
                attribute_values = struct.unpack('d' * 32,
                                                 exr_file.read(4 * 32))
                metadata[attribute_name] = attribute_values


            elif attribute_type == b'preview':

                width = struct.unpack('I', exr_file.read(4 * 1))[0]
                height = struct.unpack('I', exr_file.read(4 * 1))[0]

                # We could add a sanity check here, because
                # preview_size should equal attribute_size-8
                preview_size = 1 * 4 * width * height

                pixel_data = struct.unpack(
                    '%dB' % preview_size, exr_file.read(preview_size))

                metadata[attribute_name] = {
                    'width': width,
                    'height': height,
                    'pixel_data': pixel_data
                }

            elif attribute_type == b'rational':
                first_part = struct.unpack('i', exr_file.read(4))
                second_part = struct.unpack('I', exr_file.read(4))
                metadata[attribute_name] = {
                    'first_num': first_part[0],
                    'second_num': second_part[0]
                }

            elif attribute_type == b'string':

                string_content = struct.unpack('c' * attribute_size,
                                               exr_file.read(attribute_size))

                metadata[attribute_name] = b''.join(string_content)

            elif attribute_type == b'stringvector':
                metadata[attribute_name] = []

                while byte_count < attribute_size:

                    string_length = int(struct.unpack('i', exr_file.read(4))[0])
                    byte_count += 4

                    string_content = struct.unpack('c' * string_length,
                                                   exr_file.read(string_length))
                    byte_count += string_length

                    # print('string length: {}'.format(string_length))
                    # print('string content: {}'.format(string_content))

                    metadata[attribute_name].append(b''.join(string_content))

            elif attribute_type == b'tiledesc':
                x_size = struct.unpack('I', exr_file.read(4 * 1))[0]
                y_size = struct.unpack('I', exr_file.read(4 * 1))[0]
                mode = struct.unpack('B', exr_file.read(1 * 1))[0]

                metadata[attribute_name] = {
                    'xSize': x_size,
                    'ySize': y_size,
                    'mode': mode
                }

            elif attribute_type == b'timecode':
                time_and_flags = struct.unpack('I', exr_file.read(4 * 1))[0]
                user_data = struct.unpack('I', exr_file.read(4 * 1))[0]

                metadata[attribute_name] = {
                    'timeAndFlags': time_and_flags,
                    'userData': user_data
                }

            elif attribute_type == b'v2i':
                vector_2d_value = struct.unpack('ii', exr_file.read(4 * 2))

                metadata[attribute_name] = []
                metadata[attribute_name].append(vector_2d_value[0])
                metadata[attribute_name].append(vector_2d_value[1])

            elif attribute_type == b'v2f':
                vector_2d_value = struct.unpack('ff', exr_file.read(4 * 2))

                metadata[attribute_name] = []
                metadata[attribute_name].append(vector_2d_value[0])
                metadata[attribute_name].append(vector_2d_value[1])

            elif attribute_type == b'v3i':
                vector_3d_value = struct.unpack('iii', exr_file.read(4 * 3))

                metadata[attribute_name] = []
                metadata[attribute_name].append(vector_3d_value[0])
                metadata[attribute_name].append(vector_3d_value[1])
                metadata[attribute_name].append(vector_3d_value[2])

            elif attribute_type == b'v3f':
                vector_3d_value = struct.unpack('fff', exr_file.read(4 * 3))

                metadata[attribute_name] = []
                metadata[attribute_name].append(vector_3d_value[0])
                metadata[attribute_name].append(vector_3d_value[1])
                metadata[attribute_name].append(vector_3d_value[2])

            elif attribute_type == b'v3d':
                vector_3d_value = struct.unpack('ddd', exr_file.read(4 * 6))

                metadata[attribute_name] = []
                metadata[attribute_name].append(vector_3d_value[0])
                metadata[attribute_name].append(vector_3d_value[1])
                metadata[attribute_name].append(vector_3d_value[2])

            else:
                logger.error(
                    'unknown attribute type: {}!!'.format(attribute_type))

                metadata[attribute_name] = 'unknown attribute type!'

                raise TypeError(
                    'unknown attribute type: {}'.format(attribute_type))

            i += 1

    finally:
        exr_file.close()

    if sys.version_info.major == 2:
        # for Python 2 each string in the result should be a byte string
        return metadata
    else:
        # for Python 3 make sure to encode all byte string to unicode string
        return convert_to_unicode_string(metadata)
