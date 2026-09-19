#!/usr/bin/env python3
import struct
import sys
import zlib

def paeth(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c

def load_png(path):
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("not a PNG")
    pos = 8
    width = height = bit_depth = color_type = None
    packed = bytearray()
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if tag == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", body[:10])
        elif tag == b"IDAT":
            packed.extend(body)
        elif tag == b"IEND":
            break
    if bit_depth != 8 or color_type not in (2, 6):
        raise SystemExit(f"unsupported PNG format: depth={bit_depth} type={color_type}")
    channels = 3 if color_type == 2 else 4
    raw = zlib.decompress(bytes(packed))
    stride = width * channels
    rows = []
    prev = bytearray(stride)
    off = 0
    for _ in range(height):
        kind = raw[off]
        off += 1
        cur = bytearray(raw[off:off + stride])
        off += stride
        for i in range(stride):
            left = cur[i - channels] if i >= channels else 0
            up = prev[i]
            ul = prev[i - channels] if i >= channels else 0
            if kind == 1:
                cur[i] = (cur[i] + left) & 255
            elif kind == 2:
                cur[i] = (cur[i] + up) & 255
            elif kind == 3:
                cur[i] = (cur[i] + ((left + up) >> 1)) & 255
            elif kind == 4:
                cur[i] = (cur[i] + paeth(left, up, ul)) & 255
            elif kind != 0:
                raise SystemExit(f"unsupported PNG filter {kind}")
        rows.append(cur)
        prev = cur
    return width, height, channels, rows

def counts(path):
    width, height, channels, rows = load_png(path)
    dark = light = green = red = 0
    for row in rows:
        for i in range(0, len(row), channels):
            r, g, b = row[i], row[i + 1], row[i + 2]
            lum = (r * 3 + g * 6 + b) // 10
            dark += lum < 60
            light += lum > 160
            green += g > r + 40 and g > b + 40
            red += r > g + 40 and r > b + 40
    return width * height, dark, light, green, red

def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: check-screen.py nonblank|green <png>")
    mode, path = sys.argv[1:]
    total, dark, light, green, red = counts(path)
    if mode == "nonblank":
        need = max(1000, total // 100)
        ok = dark >= need and light >= need
    elif mode == "green":
        need = max(5000, total // 200)
        ok = green >= need and green > red * 2
    else:
        raise SystemExit("unknown mode")
    print(f"pixels={total} dark={dark} light={light} green={green} red={red}")
    return 0 if ok else 1

sys.exit(main())
