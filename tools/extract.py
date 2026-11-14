"""모든 그룹의 영어 LTR(fl 0/1) 추출 -> work/texts.json, translation/source.tsv(고유 영문, 등장 횟수)."""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__)); import gd, ltr, scsu
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
f = open(gd.ISO, 'rb'); files = []; cnt = collections.Counter(); first = {}
for nm, sz, sec, _ in gd.groups(f):
    if not sz: continue
    d, t1, E = gd.toc(f, sec, sz)
    for e in E:
        if e['typ'] != 'LTR' or e['fl'] & 0xF0: continue
        s = t1[e['idx']][0]; f.seek((gd.BASE + s) * 2048); raw = f.read(e['size'])
        if raw[:4] != b'LANG': continue
        ch = ltr.chunks(raw)
        if len(ch) != 1: continue      # 언어선택(다국어)·일본어 파일 제외
        items = [(h, scsu.decode(x)) for h, x in ltr.entries(ch[0][1])]
        if any(0x3040 <= ord(c) < 0xA000 for h, u in items for c in u): continue
        files.append(dict(group=nm, i=e['i'], fl=e['fl'], sector=s, size=e['size'], items=[[h, u] for h, u in items]))
        for h, u in items:
            cnt[u] += 1; first.setdefault(u, (nm, e['i']))
json.dump(files, open(os.path.join(R, 'work', 'texts.json'), 'w', encoding='utf8'), ensure_ascii=False)
print(len(files), 'files', len(cnt), 'unique', sum(len(k) for k in cnt), 'chars')
