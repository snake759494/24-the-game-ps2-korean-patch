"""번역 검증: 모든 묶음 id 존재, 마크업(@x/@z/@c/@j/@R@G@B/@|/@$) 보존, 줄바꿈 수, 남은 @E/@U, 금지 문자."""
import os, re, json, glob, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOK = re.compile(r'@(x....|z....|[cC]\d+|[RGB]\d+|j[lrc]|\||\$)')


def unesc(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            c = s[i+1]
            out.append({'n': '\n', 't': '\t', '\\': '\\'}.get(c, '\\' + c))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def load():
    src = json.load(open(os.path.join(R, 'translation', 'source.json'), encoding='utf8'))
    ko = {}
    for fn in sorted(glob.glob(os.path.join(R, 'translation', 'ko', '*.tsv'))):
        for ln, line in enumerate(open(fn, encoding='utf8').read().split('\n')):
            if not line.strip():
                continue
            i, _, t = line.partition('\t')
            ko[int(i)] = unesc(t)
    over = os.path.join(R, 'translation', 'override.tsv')
    if os.path.exists(over):
        for line in open(over, encoding='utf8').read().split('\n'):
            if line.strip() and not line.startswith('#'):
                i, _, t = line.partition('\t')
                ko[int(i)] = unesc(t)
    return src, ko


if __name__ == '__main__':
    src, ko = load()
    need = []
    for fn in sorted(glob.glob(os.path.join(R, 'translation', 'batches', '*.tsv'))):
        for line in open(fn, encoding='utf8').read().split('\n'):
            if line.strip():
                need.append(int(line.split('\t')[0]))
    miss = [i for i in need if i not in ko]
    print('need', len(need), 'have', len(ko), 'missing', miss[:30])
    bad = 0
    for i in need:
        if i not in ko:
            continue
        e, k = src[i], ko[i]
        te = sorted(m.group() for m in TOK.finditer(e))
        tk = sorted(m.group() for m in TOK.finditer(k))
        prob = []
        if te != tk:
            prob.append('markup %s -> %s' % (te, tk))
        if '@E' in k or '@U' in k:
            prob.append('@E/@U left')
        if e.count('\n') != k.count('\n'):
            prob.append('newline %d->%d' % (e.count('\n'), k.count('\n')))
        if '\t' in k:
            prob.append('tab')
        if prob:
            bad += 1
            if '-v' in sys.argv or bad < 60:
                print(i, prob, repr(e[:80]), '=>', repr(k[:80]))
    print('problems', bad)
