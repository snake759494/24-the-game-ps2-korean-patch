"""EE 메모리 힙 분석: 블록 = 32바이트 헤더 [prev][next][0][0][크기|0x80000000(사용)][?][태그][자기주소] + 데이터."""
import sys, struct, os, collections
sys.path.insert(0, os.path.dirname(__file__))
import emu


def blocks(m, start):
    seen = set()
    a = start
    # 처음으로 거슬러 올라감
    while True:
        prev = struct.unpack_from('<I', m, a)[0]
        if prev == 0 or prev in seen or prev >= len(m):
            break
        seen.add(prev)
        a = prev
    out = []
    seen = set()
    while a and a not in seen and a < len(m):
        seen.add(a)
        prev, nxt, z0, z1, sz, x, tag, me = struct.unpack_from('<8I', m, a)
        out.append((a, sz & 0x7fffffff, bool(sz & 0x80000000), nxt))
        a = nxt
    return out


if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else emu.latest()
    m = emu.eemem(p)
    # 힙 블록 후보: [prev][next] 이고 +0x1c 가 자기주소인 곳을 찾아 체인별로 묶음
    starts = []
    for a in range(0x100000, len(m) - 32, 16):
        me = struct.unpack_from('<I', m, a + 0x1c)[0]
        if me == a and struct.unpack_from('<I', m, a + 0x14)[0] == 0x10200000:
            starts.append(a)
    print('candidate headers', len(starts))
    chains = {}
    done = set()
    for s in starts:
        if s in done:
            continue
        bl = blocks(m, s)
        for b in bl:
            done.add(b[0])
        chains[bl[0][0]] = bl
    for k, bl in sorted(chains.items(), key=lambda kv: -len(kv[1]))[:8]:
        used = sum(b[1] for b in bl if b[2])
        free = [b for b in bl if not b[2]]
        print('chain %08x blocks %d range %08x-%08x used %d free %d maxfree %d' % (
            k, len(bl), min(b[0] for b in bl), max(b[0] + b[1] for b in bl), used,
            sum(b[1] for b in free), max([b[1] for b in free] or [0])))
