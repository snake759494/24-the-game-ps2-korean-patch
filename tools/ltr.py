"""LTR(.ltr): 'LANG' u32 0 u32 (크기-12) 이후 청크 [tag][u32 len][data](4정렬).
LNG1 데이터 = 항목들: [u32 해시][u8 (UTF16길이+5)//4][u16 바이트길이(널 포함)][SCSU 바이트]
FBM1 = 폰트(글리프 PSM0 은 파일 시작 기준 16바이트 정렬)."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import scsu

Z = bytes(1)


def chunks(b):
    assert b[:4] == b'LANG'
    end = struct.unpack_from('<I', b, 8)[0] + 12
    o = 12
    out = []
    while o + 8 <= end:
        tag = b[o:o+4]
        n = struct.unpack_from('<I', b, o+4)[0]
        out.append([tag, b[o+8:o+8+n], o + 8])
        o += 8 + n
        o = (o + 3) & ~3
    return out


def entries(data):
    o = 0
    out = []
    while o + 7 <= len(data):
        h, w, n = struct.unpack_from('<IBH', data, o)
        if n == 0:
            break
        out.append((h, data[o+7:o+7+n-1]))
        o += 7 + n
    return out


def entry(h, s):
    c = len(scsu.decode(s))
    return struct.pack('<IBH', h, (c + 5)//4, len(s) + 1) + s + Z


def build_fonts(lng1_body, fonts):
    """fonts: [(fid, 높이, recs, imgs)] -> LTR 바이트."""
    import fbm
    out = bytearray(b'LANG' + Z*8)
    body = lng1_body + Z * (-len(lng1_body) % 4)
    out += b'LNG1' + struct.pack('<I', len(body)) + body
    for fid, h, recs, imgs in fonts:
        data = fbm.build(fid, h, recs, imgs, base=len(out) + 8)
        c = b'FBM1' + struct.pack('<I', len(data)) + data
        out += c + Z * (-len(c) % 4)
    struct.pack_into('<I', out, 8, len(out) - 12)
    return bytes(out)
