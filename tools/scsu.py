"""SCSU (Unicode TR#6) 디코더/간단 인코더."""
STATIC = [0x0000, 0x0080, 0x0100, 0x0300, 0x2000, 0x2080, 0x2100, 0x3000]
DYN0 = [0x0080, 0x00C0, 0x0400, 0x0600, 0x0900, 0x3040, 0x30A0, 0xFF00]
def _off(x):
    if x == 0: return None
    if x < 0x68: return x * 0x80
    if x < 0xA8: return x * 0x80 + 0xAC00
    return {0xF9: 0xC0, 0xFA: 0x250, 0xFB: 0x370, 0xFC: 0x530, 0xFD: 0x3040, 0xFE: 0x30A0, 0xFF: 0xFF60}.get(x)
def decode(b):
    dyn = DYN0[:]; win = 0; uni = False; i = 0; out = []
    while i < len(b):
        c = b[i]; i += 1
        if not uni:
            if c in (0, 9, 10, 13) or 0x20 <= c < 0x80: out.append(c)
            elif c >= 0x80: out.append(dyn[win] + c - 0x80)
            elif 1 <= c <= 8:
                d = b[i]; i += 1
                out.append(STATIC[c-1] + d if d < 0x80 else dyn[c-1] + d - 0x80)
            elif 0x10 <= c <= 0x17: win = c - 0x10
            elif 0x18 <= c <= 0x1F: win = c - 0x18; dyn[win] = _off(b[i]); i += 1
            elif c == 0x0E: out.append(b[i] << 8 | b[i+1]); i += 2
            elif c == 0x0F: uni = True
            elif c == 0x0B: raise ValueError('SDX')
            elif c == 0x0C: raise ValueError('reserved')
        else:
            if 0xE0 <= c <= 0xE7: win = c - 0xE0; uni = False
            elif 0xE8 <= c <= 0xEF: win = c - 0xE8; dyn[win] = _off(b[i]); i += 1; uni = False
            elif c == 0xF0: out.append(b[i] << 8 | b[i+1]); i += 2
            elif c == 0xF1: raise ValueError('UDX')
            else: out.append(c << 8 | b[i]); i += 1
    return ''.join(map(chr, out))
def encode(s):
    """창 0(U+0080) 고정. ASCII/Latin-1 단일바이트, ’… 등은 SQ4, 그 외(한글 등)는 유니코드 모드."""
    out = bytearray(); uni = False
    for ch in s:
        u = ord(ch)
        if u < 0x100 and (u in (0, 9, 10, 13) or 0x20 <= u):
            if uni: out.append(0xE0); uni = False
            out.append(u)  # 0x80~0xFF: 창0(=U+0080) 이므로 그대로
        elif 0x2000 <= u < 0x2080 and not uni:
            out += bytes([5, u - 0x2000])
        else:
            if not uni: out.append(0x0F); uni = True
            hi = u >> 8
            if 0xE0 <= hi <= 0xF2: out += bytes([0xF0, hi, u & 0xFF])
            else: out += bytes([hi, u & 0xFF])
    if uni: out.append(0xE0)
    return bytes(out)
