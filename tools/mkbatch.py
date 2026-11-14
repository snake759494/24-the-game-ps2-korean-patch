"""고유 영문을 등장 순서(그룹·파일 순)로 묶음 파일로 저장.
translation/batches/NN.tsv: id <TAB> 그룹 <TAB> 영문 (줄바꿈은 \\n 로 표기)"""
import json, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(os.path.join(R, 'work', 'texts.json'), encoding='utf8'))
seen = {}
order = []
for x in F:
    for h, u in x['items']:
        if u in seen:
            continue
        seen[u] = len(order)
        order.append((u, x['group'].replace('.group.toc', '')))

MARK = re.compile(r'@(x....|z....|[cC]\d+|E|U|[RGB]\d+|j[lrc]|\||\$)')


def need(u):
    t = MARK.sub('', u)
    return bool(re.search('[A-Za-z]{2,}', t))


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')


json.dump([u for u, g in order], open(os.path.join(R, 'translation', 'source.json'), 'w', encoding='utf8'),
          ensure_ascii=False, indent=0)
b = []
cur = []
size = 0
for i, (u, g) in enumerate(order):
    if not need(u):
        continue
    cur.append((i, g, u))
    size += len(u)
    if size > 5200:
        b.append(cur)
        cur = []
        size = 0
if cur:
    b.append(cur)
for k, rs in enumerate(b):
    with open(os.path.join(R, 'translation', 'batches', '%02d.tsv' % k), 'w', encoding='utf8', newline='\n') as f:
        for i, g, u in rs:
            f.write('%d\t%s\t%s\n' % (i, g, esc(u)))
print(len(order), 'unique', sum(len(x) for x in b), 'rows in', len(b), 'batches')
