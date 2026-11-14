"""GAMEDATA(TOCSM/TOC0) 읽기. GAMEDATA.1/.2 는 ISO 안에서 연속(섹터 3220부터)."""
import struct, collections
ISO = r'D:\ps2\24_더게임\24 - The Game (USA) (En,Fr,Es).iso'
BASE = 3220
def groups(f):
    f.seek(BASE*2048); d = f.read(0x1000); out = []; o = 16
    while d[o:o+1].isalpha():
        nm = d[o:o+32].split(b'\0')[0].decode(); sz, sec = struct.unpack_from('<II', d, o+32)
        out.append((nm, sz, sec, BASE*2048 + o)); o += 40
    return out
def toc(f, sec, sz):
    f.seek((BASE+sec)*2048); d = f.read(sz)
    n1, n2 = struct.unpack_from('<II', d, 4); t1 = []; ents = []
    for i in range(n1):
        a, idx, ff = struct.unpack_from('<IHH', d, 16+i*8); t1.append((a & 0xffffff, a >> 24, idx, ff))
    for i in range(n2):
        h, size, typ, fl, idx2, c1, c2 = struct.unpack_from('<II4sHHHH', d, 16+n1*8+i*20)
        ents.append(dict(i=i, hash=h, size=size, typ=typ.rstrip(b'\0').decode('latin1'), fl=fl, idx=idx2, c1=c1, c2=c2))
    return d, t1, ents
