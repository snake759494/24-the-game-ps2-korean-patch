"""한글 글리프 생성: 폰트ID별 서체·크기·기준선. 4배 오버샘플 후 16단계 농도로 축소."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def F(n): return os.path.join(R, n)
# fid: (ttf, 픽셀크기(em), 글자 윗선 y, 기울임, 굵게(px))
SPEC = {
    0: ('NanumSquareNeo-eHv.ttf', 17, 2, 0.0),
    1: ('NanumSquareNeo-eHv.ttf', 17, 2, 0.0),
    2: ('NanumSquareNeo-eHv.ttf', 19, 5, 0.0),
    3: ('NanumSquareNeo-bRg.ttf', 17, 5, 0.0),
    4: ('NanumSquareNeo-bRg.ttf', 21, 3, 0.0),
    5: ('NanumSquareNeo-bRg.ttf', 20, 4, 0.0),
    6: ('NanumSquareNeo-bRg.ttf', 20, 4, 0.0),
    7: ('NanumSquareNeo-bRg.ttf', 20, 4, 0.0),
    9: ('NanumSquareNeo-cBd.ttf', 19, 1, 0.0),
}
# 본문 폰트는 굵은 서체를 쓰되 전진폭은 원래 서체(dEb) 기준으로 제한:
# 폭이 넓어지면 튜토리얼 패널 등에서 줄 넘침으로 게임이 멈춤
ADVREF = {0: ('NanumSquareNeo-dEb.ttf', 17, 2, 0.0), 1: ('NanumSquareNeo-dEb.ttf', 17, 2, 0.2)}
_cache = {}
def glyph(fid, ch):
    """(32x32 0..15 배열, 전진폭)"""
    ttf, size, top, skew = SPEC[fid]
    S = 4
    key = (ttf, size)
    if key not in _cache: _cache[key] = ImageFont.truetype(F(ttf), size * S)
    font = _cache[key]
    im = Image.new('L', (32*S, 32*S), 0); d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), '가', font=font)      # 한글 높이 기준(모든 글자 동일 위치)
    d.text((S*1 - bb[0], top*S - bb[1]), ch, font=font, fill=255)
    if skew:
        im = im.transform(im.size, Image.AFFINE, (1, skew, -skew*top*S*1.0 - skew*size*S*0.5, 0, 1, 0), Image.BICUBIC)
    a = np.asarray(im.resize((32, 32), Image.BOX), np.float32) / 255.0
    a = np.clip(a * 1.35, 0, 1) ** 0.8          # 획 농도 강화(가독성)
    p = np.clip(np.round(a * 15), 0, 15).astype(np.uint8)
    if os.environ.get('FONTMARK') and fid in (1, 2, 3, 4):  # 진단용: 폰트별 표시
        if fid == 1: p[1, 0:20] = p[22, 0:20] = 15; p[1:23, 0] = p[1:23, 19] = 15
        if fid == 2: p[23:25, 0:20] = 15
        if fid == 3: p[0:2, 0:20] = 15
        if fid == 4: p[0:24, 0:2] = 15
    xs = np.nonzero(p.any(0))[0]
    adv = (int(xs.max()) + 2) if len(xs) else size // 2
    if fid in ADVREF:
        SPEC['ref'] = ADVREF[fid]
        adv = min(adv, glyph('ref', ch)[1])
    return p, adv
