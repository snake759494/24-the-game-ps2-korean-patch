"""GAMEDATA 파일 교체기.
목차(그룹 TOC0): t1[k] = (섹터 | b<<24, E번호, ff), E[i] = (해시, 크기, 타입, ...), E[i].idx = t1 번호.
파일은 섹터 정렬 연속 배치. 새 데이터가 원래 할당 섹터에 들어가면 제자리, 아니면 디스크 끝(GAMEDATA.2 뒤)에 추가.
GAMEDATA.1 과 .2 는 ISO 에서 연속이므로 섹터 = ISO 섹터 - BASE."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gd, iso, udf

SEC = 2048


class Disc:
    def __init__(self, path):
        self.f = open(path, 'r+b')
        self.groups = {g[0]: g for g in gd.groups(self.f)}
        self.tocs = {}
        self.end = os.path.getsize(path) // SEC          # 다음 추가 위치(ISO 섹터)
        self.recs = iso.records(self.f)

    def toc(self, gname):
        if gname not in self.tocs:
            nm, sz, sec, _ = self.groups[gname]
            d, t1, E = gd.toc(self.f, sec, sz)
            self.tocs[gname] = [bytearray(d), t1, E, sec]
        return self.tocs[gname]

    def loc(self, gname, i):
        d, t1, E, sec = self.toc(gname)
        e = E[i]
        return t1[e['idx']][0], e['size']

    def read(self, gname, i):
        s, size = self.loc(gname, i)
        self.f.seek((gd.BASE + s) * SEC)
        return self.f.read(size)

    def write_at(self, sector, data):
        self.f.seek((gd.BASE + sector) * SEC)
        self.f.write(data + bytes((-len(data)) % SEC))

    def append(self, data):
        s = self.end - gd.BASE
        self.f.seek(self.end * SEC)
        self.f.write(data + bytes((-len(data)) % SEC))
        self.end += (len(data) + SEC - 1) // SEC
        return s

    def point(self, gname, i, sector, size):
        """E[i] 를 sector/size 로 지정"""
        d, t1, E, sec = self.toc(gname)
        n1 = len(t1)
        e = E[i]
        k = e['idx']
        a = struct.unpack_from('<I', d, 16 + k*8)[0]
        struct.pack_into('<I', d, 16 + k*8, (a & 0xff000000) | sector)
        struct.pack_into('<I', d, 16 + n1*8 + i*20 + 4, size)
        t1[k] = (sector,) + tuple(t1[k][1:])
        e['size'] = size

    def replace(self, gname, i, data, inplace_cap=None):
        s, size = self.loc(gname, i)
        cap = inplace_cap if inplace_cap is not None else (size + SEC - 1) // SEC * SEC
        if len(data) <= cap:
            self.write_at(s, data)
            ns = s
        else:
            ns = self.append(data)
        self.point(gname, i, ns, len(data))
        return ns

    def close(self):
        for gname, (d, t1, E, sec) in self.tocs.items():
            self.f.seek((gd.BASE + sec) * SEC)
            self.f.write(d)
        total = self.end
        self.f.seek(total * SEC - 1)
        self.f.write(b'\0')
        # GAMEDATA.2 크기 = 끝까지
        lba, sz, roff = self.recs['GAMEDATA.2']
        nsz = total * SEC - lba * SEC
        self.f.seek(roff + 10)
        self.f.write(struct.pack('<I', nsz) + struct.pack('>I', nsz))
        # PVD 볼륨 크기
        self.f.seek(16 * SEC + 80)
        self.f.write(struct.pack('<I', total + 1) + struct.pack('>I', total + 1))
        u = udf.UDF(self.f)
        u.set_file('/GAMEDATA.2', lba, nsz)
        u.grow(total + 1)
        self.f.seek((total + 1) * SEC - 1)
        self.f.write(b'\0')
        self.f.close()
