"""Bounded PNG validation without a new runtime dependency. No geometry side effects."""
import struct
import zlib


def dimensions(path):
    data=path.read_bytes()
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Invalid PNG signature')
    pos=8;header=None;compressed=[];ended=False
    while pos<len(data):
        if pos+12>len(data):raise ValueError('Truncated PNG chunk')
        size=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];end=pos+8+size
        if end+4>len(data):raise ValueError('Truncated PNG data')
        block=data[pos+8:end]
        if zlib.crc32(kind+block)&0xffffffff!=struct.unpack('>I',data[end:end+4])[0]:raise ValueError('PNG checksum mismatch')
        if header is None:
            if kind!=b'IHDR' or size!=13:raise ValueError('PNG header missing')
            header=struct.unpack('>IIBBBBB',block)
        elif kind==b'IHDR':raise ValueError('Duplicate PNG header')
        if kind==b'IDAT':compressed.append(block)
        if kind==b'IEND':
            if size or end+4!=len(data):raise ValueError('Invalid PNG end')
            ended=True;break
        pos=end+4
    if not header or not ended or not compressed:raise ValueError('Incomplete PNG')
    w,h,depth,color,compression,filter_method,interlace=header
    if not 0<w<=8192 or not 0<h<=8192:raise ValueError('PNG dimensions outside bound')
    if depth!=8 or color not in (0,2,4,6) or compression or filter_method or interlace:
        raise ValueError('PNG decoding unproven: only non-interlaced 8-bit gray/RGB/alpha supported')
    channels={0:1,2:3,4:2,6:4}[color];stride=w*channels+1;expected=stride*h
    decoder=zlib.decompressobj();pixels=decoder.decompress(b''.join(compressed),expected+1)
    if len(pixels)!=expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('PNG raster size/compression invalid')
    if any(pixels[i] not in range(5) for i in range(0,expected,stride)):raise ValueError('Invalid PNG scanline filter')
    return w,h
