"""FBM1 폰트: [u16 개수][u8 폰트ID][u8 높이] + 개수×[u16 코드][u16 폭][u8 a][u8 b][u8 c][u8 전진폭] + 16정렬 + 글리프별 PSM0.
(단독 파일은 앞에 'FBM1' u32 길이가 붙음). PSM0: 32바이트 헤더(w,h) + 16색 CLUT(64) + 4bpp 픽셀."""
import struct
def parse(data, base=0, absoff=0):
    n, fid, h = struct.unpack_from('<HBB', data, base)
    recs = [struct.unpack_from('<HHBBBB', data, base + 4 + i*8) for i in range(n)]
    o = base + 4 + n*8; o += (-(o + absoff)) % 16
    imgs = []
    for i in range(n):
        assert data[o:o+4] == b'PSM0', (i, hex(o), data[o:o+8])
        w, hh = struct.unpack_from('<HH', data, o+8)
        size = 32 + 64 + w*hh//2
        imgs.append(data[o:o+size]); o += size
    return fid, h, recs, imgs, o
def psm0(pix, w=32, h=32):
    """pix: h×w 0..15 값."""
    hdr = b'PSM0' + struct.pack('<HHHHIIHH', 0, 0x14, w, h, 1, 0x40000, 8, 2) + b'\0'*8
    clut = b''.join(bytes([v*17, v*17, v*17, 0x80]) for v in range(16))
    px = bytearray()
    for y in range(h):
        for x in range(0, w, 2): px.append((pix[y][x] & 15) | ((pix[y][x+1] & 15) << 4))
    return hdr + clut + bytes(px)
def build(fid, h, recs, imgs, base=0):
    """base = 이 데이터의 파일 내 시작 위치(PSM0 은 파일 기준 16정렬)."""
    out = struct.pack('<HBB', len(recs), fid, h) + b''.join(struct.pack('<HHBBBB', *r) for r in recs)
    out += b'\0' * ((-(base + len(out))) % 16)
    return out + b''.join(imgs)
def topix(img):
    w, h = struct.unpack_from('<HH', img, 8); px = img[96:]
    return [[(px[(y*w+x)//2] >> (4*(x & 1))) & 15 for x in range(w)] for y in range(h)]

import numpy as np
_IDX = None
def _idx():
    """32x32 PSMT4 픽셀 -> (CT32 16x8 로 올린 데이터의) 니블 주소."""
    global _IDX
    if _IDX is None:
        import gsmem
        # CT32 16x8 rect @bp0 bw1 의 바이트주소 -> 데이터 바이트 오프셋
        inv = {}
        for y in range(8):
            for x in range(16):
                a = gsmem.addr32(0, 1, x, y)
                for k in range(4): inv[a + k] = (y*16 + x)*4 + k
        idx = np.zeros((32, 32), np.int64)
        for y in range(32):
            for x in range(32):
                n = gsmem.addr4(0, 1, x, y); idx[y, x] = inv[n >> 1]*2 + (n & 1)
        _IDX = idx
    return _IDX
def topix(img):
    w, h = struct.unpack_from('<HH', img, 8); assert (w, h) == (32, 32), (w, h)
    b = np.frombuffer(img[96:96+512], np.uint8); n = _idx()
    v = b[n >> 1]; return np.where(n & 1, v >> 4, v & 15).astype(np.uint8)
def frompix(p):
    """32x32 (0..15) -> PSM0 바이트."""
    n = _idx(); out = np.zeros(512, np.uint8)
    p = np.asarray(p, np.uint8) & 15
    lo = (n & 1) == 0
    np.add.at(out, (n[lo] >> 1), p[lo]); np.add.at(out, (n[~lo] >> 1), p[~lo] << 4)
    hdr = b'PSM0' + struct.pack('<HHHHIIHH', 0, 0x14, 32, 32, 1, 0x40000, 8, 2) + b'\0'*8
    clut = b''.join(bytes([v*17, v*17, v*17, 0x80]) for v in range(16))
    return hdr + clut + out.tobytes()
