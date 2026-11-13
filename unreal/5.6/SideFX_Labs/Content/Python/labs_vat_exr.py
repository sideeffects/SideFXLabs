"""Bounded OpenEXR header reader. Pixel decoding remains Unreal's responsibility.

The VAT importer supports only ordinary single-part scanline EXRs.
No sidecar JSON discovery, third-party module, or pixel conversion occurs here.
"""
import json
import math
import struct
from pathlib import Path


class ValidationError(ValueError):
    pass


def read_header(path):
    with Path(path).open('rb') as stream:
        size = stream.seek(0, 2)
        stream.seek(0)
        def read(n):
            if n < 0 or n > size-stream.tell():
                raise ValidationError('Truncated EXR header')
            data = stream.read(n)
            if len(data) != n:
                raise ValidationError('Truncated EXR header')
            return data
        if read(4) != struct.pack('<I', 20000630):
            raise ValidationError('Not an OpenEXR file')
        version = struct.unpack('<I', read(4))[0]
        if version & 255 != 2 or version & ~0x4FF:
            raise ValidationError('Only single-part, non-deep scanline EXR is supported')
        limit = 255 if version & 0x400 else 31
        def string():
            data = bytearray()
            for _ in range(limit+1):
                c=read(1)
                if c == b'\0':
                    try: return data.decode('utf-8')
                    except UnicodeDecodeError as exc: raise ValidationError('Invalid EXR name') from exc
                data.extend(c)
            raise ValidationError('Overlong EXR header name')
        attrs={}
        while True:
            if stream.tell() > 4*1024*1024 or len(attrs)>1024:
                raise ValidationError('EXR header exceeds safety limits')
            name=string()
            if not name: break
            kind=string()
            length=struct.unpack('<i',read(4))[0]
            if length<0 or length>4*1024*1024 or name in attrs:
                raise ValidationError('Invalid/duplicate EXR attribute')
            attrs[name]=(kind,read(length))
        if 'dataWindow' not in attrs or attrs['dataWindow'][0]!='box2i' or len(attrs['dataWindow'][1])!=16:
            raise ValidationError('Missing or invalid EXR dataWindow')
        x0,y0,x1,y1=struct.unpack('<4i',attrs['dataWindow'][1])
        dimensions=(x1-x0+1,y1-y0+1)
        if not all(0 < n <= 2147483647 for n in dimensions):
            raise ValidationError('Invalid EXR dimensions')
        payload=None
        if 'sidefx_labs_velocity' in attrs:
            kind,data=attrs['sidefx_labs_velocity']
            if kind!='string' or not 0<len(data)<=65536:
                raise ValidationError('Invalid velocity metadata attribute')
            try:
                payload=json.loads(data.decode('utf-8'), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
            except (UnicodeError,ValueError) as exc:
                raise ValidationError('Malformed embedded velocity JSON') from exc
        return dimensions,payload


def velocity_info(velocity, position, entered_fps):
    dimensions,payload=read_header(velocity)
    if dimensions != read_header(position)[0]:
        raise ValidationError('Velocity and Position atlas dimensions must match')
    def number(value):
        return type(value) in (int,float) and math.isfinite(value)
    if payload is None:
        if not number(entered_fps) or entered_fps<=0:
            raise ValidationError('Enter a finite positive Houdini FPS')
        return {'fps':float(entered_fps),'dimensions':dimensions,'embedded':False}
    if not isinstance(payload,dict) or payload.get('schema')!='sidefx-labs-fluid-velocity-1':
        raise ValidationError('Unsupported embedded velocity schema')
    v=payload.get('velocity')
    expected={'present':True,'coordinates':'houdini-local','units':'houdini-units-per-second','layout':'position-atlas'}
    if not isinstance(v,dict) or any(v.get(k)!=value for k,value in expected.items()) or v.get('present') is not True:
        raise ValidationError('Incompatible embedded velocity convention')
    if not isinstance(v.get('file'),str) or not v['file']:
        raise ValidationError('Missing velocity filename metadata')
    if not all(number(v.get(k)) for k in ['fps','width','height','frame_start','frame_end']):
        raise ValidationError('Invalid numerical velocity metadata')
    if v['fps']<=0 or (v['width'],v['height'])!=dimensions or v['frame_end']<v['frame_start']:
        raise ValidationError('Incompatible velocity dimensions, FPS or frame range')
    return {'fps':float(v['fps']),'dimensions':dimensions,'embedded':True}
