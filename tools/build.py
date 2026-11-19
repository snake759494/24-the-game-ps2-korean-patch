"""24: The Game 한글 패치 빌드.
1) 원본 ISO 복사 -> 24 - The Game (USA) (Korean).iso (원본과 같은 폴더)
2) 모든 그룹의 영어 LTR 을 한국어로 다시 만들어, 같은 자리의 프랑스어·스페인어·영어 3칸(연속 영역)에 쓰고
   세 언어 항목 모두 한국어 파일을 가리키게 함(영역이 모자라면 디스크 끝에 추가)
3) 기본 폰트(FBM1)에 번역문에 쓰인 한글 글리프를 추가해 디스크 끝으로 재배치
4) GAMEDATA.2 / 볼륨 크기 / UDF 갱신
사용: python tools/build.py [--out 경로] [--nocopy]"""
import os, sys, struct, json, shutil, time, collections
sys.path.insert(0, os.path.dirname(__file__))
import gd, ltr, scsu, fbm, kfont, disc, check

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = gd.ISO
OUT = os.path.join(R, '24 - The Game (USA) (Korean).iso')
SEC = 2048

# 한글을 넣을 폰트 파일(movies_1 그룹 E 번호): 세트 A 0~4, 세트 B 0~4, 고정폭 5~7 두 세트
FONT_FILES = [2335, 2336, 2337, 2338, 2339]
FONT_GROUP = 'movies_1.group.toc'


def caps_chars(tr, maxlen=999):
    """제목·메뉴(영어 원문이 모두 대문자)에 쓰인 글자: 메모리 때문에 fid2~4 에는 이것만 넣음"""
    import re
    out = set()
    for e, k in tr.items():
        e2 = re.sub(r'@(x....|z....|[cC]\d+|[RGB]\d+|j[lrc]|\||\$|E|U)', '', e)
        l = [c for c in e2 if c.isalpha()]
        if l and all(c.isupper() for c in l) and len(k) <= maxlen:
            out.update(k)
    return out


def translations():
    src, ko = check.load()
    return {src[i]: ko[i] for i in ko}


def text_files(D):
    """(그룹, E번호) 목록: 영어 LTR(단일 LNG1, 일본어 아님)"""
    out = []
    for gname, g in D.groups.items():
        if not g[1]:
            continue
        d, t1, E, sec = D.toc(gname)
        for e in E:
            if e['typ'] != 'LTR' or e['fl'] & 0xF0:
                continue
            raw = D.read(gname, e['i'])
            if raw[:4] != b'LANG':
                continue
            ch = ltr.chunks(raw)
            if len(ch) != 1:
                continue
            items = [(h, scsu.decode(x)) for h, x in ltr.entries(ch[0][1])]
            if any(0x3040 <= ord(c) < 0xA000 for h, u in items for c in u):
                continue
            out.append((gname, e['i'], items))
    return out


def keyset(D, gname, j):
    raw = D.read(gname, j)
    if raw[:4] != b'LANG':
        return None
    ch = ltr.chunks(raw)
    if len(ch) != 1 or ch[0][0] != b'LNG1':
        return None
    return tuple(h for h, x in ltr.entries(ch[0][1]))


def siblings(D, gname, i, keys):
    """같은 문자열 해시 목록을 가진 프랑스어·스페인어 LTR 중 영어 파일과 맞닿은 연속 영역.
    반환: [E번호], 시작섹터, 용량(바이트). (원본 목차 기준으로 호출할 것)"""
    d, t1, E, sec = D.toc(gname)
    fl = E[i]['fl']
    group = [i]
    for j in range(max(0, i - 6), min(len(E), i + 7)):
        if j != i and E[j]['typ'] == 'LTR' and E[j]['fl'] in (fl | 16, fl | 64) and keyset(D, gname, j) == keys:
            group.append(j)
    ext = sorted((t1[E[j]['idx']][0], (E[j]['size'] + SEC - 1) // SEC, j) for j in group)
    runs = [[ext[0]]]
    for x in ext[1:]:
        p = runs[-1][-1]
        if x[0] == p[0] + p[1]:
            runs[-1].append(x)
        else:
            runs.append([x])
    run = [r for r in runs if any(x[2] == i for x in r)][0]
    return [x[2] for x in run], run[0][0], sum(x[1] for x in run) * SEC


def build_fonts(D, charsets, log):
    d, t1, E, sec = D.toc(FONT_GROUP)
    for i in FONT_FILES:
        raw = D.read(FONT_GROUP, i)
        assert raw[:4] == b'FBM1', (i, raw[:4])
        fid, h, recs, imgs, end = fbm.parse(raw, 8, 0)
        chars = charsets.get(fid, charsets['small'])
        # 메모리 확보: 번역문에 쓰이지 않는 확장 문자(프랑스어·스페인어 악센트 등) 글리프 제거
        keep = [k for k, r in enumerate(recs) if r[0] <= 0x7e or chr(r[0]) in charsets['used']]
        if chars is None:  # 글리프를 fid0 과 공유(ELF 패치): 파일에는 글리프를 두지 않음
            keep, chars = [], []
        recs = [recs[k] for k in keep]
        imgs = [imgs[k] for k in keep]
        have = {r[0] for r in recs}
        add = [c for c in chars if ord(c) not in have]
        for c in add:
            p, adv = kfont.glyph(fid, c)
            recs.append((ord(c), adv, 0, 0, 0, adv))
            imgs.append(fbm.frompix(p))
        order = sorted(range(len(recs)), key=lambda k: recs[k][0])
        recs = [recs[k] for k in order]
        imgs = [imgs[k] for k in order]
        data = fbm.build(fid, h, recs, imgs, base=8)
        data = b'FBM1' + struct.pack('<I', len(data)) + data
        ns = D.replace(FONT_GROUP, i, data)
        log.append('font E%d fid%d +%d glyphs -> sector %d (%d bytes)' % (i, fid, len(add), ns, len(data)))


# 폰트 슬롯 생성 루프(0x4473d0)에서 새 슬롯 {높이, 글리프셋} 을 채우는 자리를
# 코드 동굴(0x4722c8, 함수 사이 nop 패딩)로 돌려, 슬롯 1·2(fid1·fid2)는 슬롯 0 의 글리프셋을 쓰게 함.
# → fid1·fid2 에 한글 글리프를 따로 둘 필요가 없어 레벨 메모리 약 1.3MB 확보.
ELF_NAME = 'SLUS_212.68'
SHARE_HOOK = 0x4475ac
SHARE_CAVE = 0x4722c8
FREE_HOOK = 0x447328


def _j(target):
    return 0x08000000 | ((target >> 2) & 0x3ffffff)


def share_glyphs(D, log):
    sec, size = D.recs[ELF_NAME][:2]
    off = lambda va: sec * SEC + va - 0x100000 + 0x80
    hook_orig = [0x6ba30007, 0x6fa30000, 0xb0430007, 0xb4430000]
    hook = [_j(SHARE_CAVE), 0x00000000, 0x00000000, 0x00000000]
    cave = [
        0x8e880010,  # lw   t0, 0x10(s4)   슬롯 수(새 슬롯 번호+1)
        0x2508fffe,  # addiu t0, t0, -2
        0x2d080002,  # sltiu t0, t0, 2      새 슬롯이 1 또는 2 이면 1
        0x8e890018,  # lw   t1, 0x18(s4)   슬롯 배열
        0x8d290004,  # lw   t1, 4(t1)      슬롯 0 의 글리프셋
        0x0268480a,  # movz t1, s3, t0     아니면 새로 만든 글리프셋
        0xac400000,  # sw   zero, 0(v0)
        _j(SHARE_HOOK + 0x10),
        0xac490004,  # sw   t1, 4(v0)       (지연 슬롯)
        # 폰트 전체 해제(0x447258)에서 슬롯 1·2 는 공유 글리프셋이므로 지우지 않음
        0x8c640004,  # lw   a0, 4(v1)
        0x2648ffff,  # addiu t0, s2, -1     s2 = 슬롯 번호
        0x2d080002,  # sltiu t0, t0, 2
        _j(FREE_HOOK + 8),
        0x0008200b,  # movn a0, zero, t0    (지연 슬롯) 슬롯 1·2 면 a0=0 → 삭제 건너뜀
    ]
    free_orig = [0x00621821, 0x8c640004]
    free_hook = [_j(SHARE_CAVE + 9 * 4), 0x00621821]
    f = D.f
    f.seek(off(SHARE_HOOK)); cur = list(struct.unpack('<4I', f.read(16)))
    assert cur == hook_orig, [hex(x) for x in cur]
    f.seek(off(SHARE_CAVE)); assert f.read(len(cave) * 4) == bytes(len(cave) * 4)
    f.seek(off(FREE_HOOK)); cur = list(struct.unpack('<2I', f.read(8)))
    assert cur == free_orig, [hex(x) for x in cur]
    f.seek(off(SHARE_HOOK)); f.write(struct.pack('<4I', *hook))
    f.seek(off(FREE_HOOK)); f.write(struct.pack('<2I', *free_hook))
    f.seek(off(SHARE_CAVE)); f.write(struct.pack('<%dI' % len(cave), *cave))
    log.append('glyph share patch: hook %x -> cave %x' % (SHARE_HOOK, SHARE_CAVE))


def main():
    args = sys.argv[1:]
    out = args[args.index('--out') + 1] if '--out' in args else OUT
    t0 = time.time()
    if '--nocopy' not in args:
        shutil.copyfile(SRC, out)
    tr = translations()
    D = disc.Disc(out)
    log = []
    files = text_files(D)
    if '--only' in args:
        lo, hi = map(int, args[args.index('--only') + 1].split(':'))
        files = files[lo:hi]
    if '--notr' in args:
        tr = {}
    # 원본 목차 기준으로 자리 계획(쓰기 전에 전부 계산)
    plans = []
    taken = {}
    for gname, i, items in files:
        sib, start, cap = siblings(D, gname, i, tuple(h for h, u in items))
        for s in range(start, start + cap // SEC):
            assert (gname, s) not in taken or taken[(gname, s)] == (start, cap), ('겹침', gname, i, s)
            taken[(gname, s)] = (start, cap)
        plans.append((sib, start, cap))
    used = set()
    stats = collections.Counter()
    for (gname, i, items), (sib, start, cap) in zip(files, plans):
        new = []
        for h, u in items:
            k = tr.get(u, u)
            for c in k:
                if ord(c) > 0x7e:
                    used.add(c)
            new.append((h, scsu.encode(k)))
            stats['tr' if u in tr else 'keep'] += 1
        body = b''.join(ltr.entry(h, s) for h, s in new)
        data = ltr.build_fonts(body, [])
        stats['sib%d' % len(sib)] += 1
        if len(data) <= cap:
            D.write_at(start, data)
            ns = start
            stats['inplace'] += 1
        else:
            ns = D.append(data)
            stats['append'] += 1
        for j in sib:
            D.point(gname, j, ns, len(data))
    hangul = sorted(c for c in used if 0xAC00 <= ord(c) <= 0xD7A3)
    other = sorted(c for c in used if not 0xAC00 <= ord(c) <= 0xD7A3)
    log.append('text files %d, %s, hangul %d, other %s' % (len(files), dict(stats), len(hangul), other))
    small = {c for c in caps_chars(tr) if ord(c) > 0x7e}
    for k in tr.values():  # 짧은 문구(제목·상태 표시 등)도 작은 세트에 포함
        if len(k) <= int(os.environ.get("SMALLLEN", 8)):
            small.update(c for c in k if ord(c) > 0x7e)
    small = sorted(small)
    # fid1(메뉴 버튼·튜토리얼 패널): 작은 세트 + 버튼/글머리 코드가 든 문구(튜토리얼·조작 안내)의 글자
    import re as _re
    caps = {c for c in caps_chars(tr) if ord(c) > 0x7e}
    tut = set(caps)  # 메뉴 버튼(영어 대문자) + 조작 안내 문구
    for e, k in tr.items():
        if _re.search(r'@[xz][A-Z_]{4}', e):
            tut.update(c for c in k if ord(c) > 0x7e)
    tut = sorted(tut)
    log.append('tutorial set %d' % len(tut))
    log.append('small set %d' % len(small))
    full = hangul + other
    title = set(caps)  # fid2(제목·장소명): 대문자 원문 + 아주 짧은 문구
    for k in tr.values():
        if len(k) <= 4:
            title.update(c for c in k if ord(c) > 0x7e)
    title = sorted(title)
    log.append('title set %d' % len(title))
    mini = sorted({c for c in caps_chars(tr, 6) if ord(c) > 0x7e})
    plan = os.environ.get('FONTPLAN', '0f,1z,2z,3n,4n')
    sets = {}
    for t in plan.split(','):
        sets[int(t[:-1])] = {'f': full, 's': small, 't': tut, 'm': mini, 'c': title, 'n': [], 'z': None}[t[-1]]
    sets['small'] = small
    sets['used'] = used
    build_fonts(D, sets, log)
    if os.environ.get('FONTSHARE', '1') == '1':
        share_glyphs(D, log)
    D.close()
    log.append('done %.1fs -> %s' % (time.time() - t0, out))
    print('\n'.join(log))


if __name__ == '__main__':
    main()
