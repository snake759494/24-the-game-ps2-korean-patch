"""검증용 휴대용 PCSX2(work/emu/pcsx2-24.exe). 최소화·비활성 실행, PINE(28524) 메모리 접근/상태저장,
상태저장 속 Screenshot.png 로 화면 확인. 입력은 가상패드(pnach 코드케이브, VPAD 주소 비트 = 눌림)."""
import subprocess, sys, os, time, glob, zipfile, struct, ctypes, socket
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMU = os.path.join(R, 'work', 'emu'); EXE = os.path.join(EMU, 'pcsx2-24.exe'); PORT = 28524
VPAD = 0x000ff000
BTN = dict(SELECT=1, L3=2, R3=4, START=8, U=0x10, R=0x20, D=0x40, L=0x80, L2=0x100, R2=0x200, L1=0x400, R1=0x800,
           T=0x1000, O=0x2000, X=0x4000, S=0x8000)
CHEAT = ''   # pnach 본문(가상패드 패치)
def elf_crc(iso):
    sys.path.insert(0, os.path.dirname(__file__)); import iso as I
    f = open(iso, 'rb'); r = I.records(f)['SLUS_212.68']; d = I.read(f, r); c = 0
    for (x,) in struct.iter_unpack('<I', d[:len(d)//4*4]): c ^= x
    return c
def launch(iso, state=None):
    stop(); crc = elf_crc(iso)
    for f in glob.glob(os.path.join(EMU, 'cheats', '*.pnach')): os.remove(f)
    if os.path.exists(os.path.join(R, 'tools', 'vpad.pnach')):
        open(os.path.join(EMU, 'cheats', '%08X.pnach' % crc), 'w').write(open(os.path.join(R, 'tools', 'vpad.pnach')).read())
    si = subprocess.STARTUPINFO(); si.dwFlags = 1; si.wShowWindow = 7   # SW_SHOWMINNOACTIVE
    args = [EXE, '-batch', '-nogui']
    if state: args += ['-statefile', state]
    p = subprocess.Popen(args + ['--', os.path.abspath(iso)], cwd=EMU, startupinfo=si)
    print('pid', p.pid, 'crc %08X' % crc); hide(p.pid)
def wins(pid):
    u = ctypes.windll.user32; hs = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h, l):
        pp = ctypes.c_ulong(); u.GetWindowThreadProcessId(ctypes.c_void_p(h), ctypes.byref(pp))
        if pp.value == pid and u.IsWindowVisible(ctypes.c_void_p(h)): hs.append(h)
        return True
    u.EnumWindows(cb, 0); return hs
def hide(pid):
    u = ctypes.windll.user32
    for _ in range(150):
        hs = wins(pid)
        if hs:
            time.sleep(1.0)
            for h in hs: u.ShowWindow(ctypes.c_void_p(h), 7)
            return
        time.sleep(0.2)
def stop():
    for _ in range(30):
        r = subprocess.run(['tasklist', '/fi', 'imagename eq pcsx2-24.exe'], capture_output=True, text=True)
        if 'pcsx2-24.exe' not in r.stdout: return
        subprocess.run(['taskkill', '/F', '/T', '/IM', 'pcsx2-24.exe'], capture_output=True); time.sleep(1)
_S = [None]
def pine(payload):
    try:
        return _pine(payload)
    except (OSError, EOFError):
        _S[0] = None; return _pine(payload)
def _pine(payload):
    if _S[0] is None: _S[0] = socket.create_connection(('127.0.0.1', PORT), timeout=20)
    s = _S[0]
    s.sendall(struct.pack('<I', len(payload) + 4) + payload)
    def rv(n):
        b = b''
        while len(b) < n:
            c = s.recv(n - len(b))
            if not c: raise EOFError
            b += c
        return b
    n = struct.unpack('<I', rv(4))[0]; body = rv(n - 4); return body
def w32(a, v): return pine(struct.pack('<BII', 6, a, v))
def r32(a): return struct.unpack_from('<I', pine(struct.pack('<BI', 2, a)), 1)[0]
def press(names, ms=200):
    m = 0
    for n in names.split('+'): m |= BTN[n]
    w32(VPAD, m); time.sleep(ms / 1000); w32(VPAD, 0); time.sleep(0.25)
def member(p, name):
    import zstandard
    with zipfile.ZipFile(p) as z: i = z.getinfo(name)
    with open(p, 'rb') as f:
        f.seek(i.header_offset); h = f.read(30); n, e = struct.unpack_from('<HH', h, 26); f.seek(n + e, 1)
        raw = f.read(i.compress_size)
    if i.compress_type == 0: return raw
    if i.compress_type == 93: return zstandard.ZstdDecompressor().decompress(raw, max_output_size=i.file_size)
    with zipfile.ZipFile(p) as z: return z.read(name)
def latest():
    ps = glob.glob(os.path.join(EMU, 'sstates', '*.p2s'))
    return max(ps, key=os.path.getmtime) if ps else None
def save(slot=9):
    old = latest(); t = os.path.getmtime(old) if old else 0
    pine(struct.pack('<BB', 9, slot))
    for _ in range(300):
        p = latest()
        if p and os.path.getmtime(p) > t: time.sleep(1.0); return p
        time.sleep(0.1)
def snap(tag, slot=9):
    p = save(slot)
    os.makedirs(os.path.join(R, 'work', 'shots'), exist_ok=True)
    out = os.path.join(R, 'work', 'shots', '%s.png' % tag)
    open(out, 'wb').write(member(p, 'Screenshot.png')); print(out); return p
def eemem(p): return member(p, 'eeMemory.bin')
if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'launch': launch(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif c == 'stop': stop()
    elif c == 'snap': snap(sys.argv[2])
    elif c == 'press':
        for k in sys.argv[2:]:
            try: time.sleep(float(k))
            except ValueError: press(k)
    elif c == 'save': print(pine(struct.pack('<BB', 9, int(sys.argv[2]))))
    elif c == 'load': print(pine(struct.pack('<BB', 0xa, int(sys.argv[2]))))
    elif c == 'rd':
        a = int(sys.argv[2], 16); print(' '.join('%08x' % r32(a + 4 * k) for k in range(int(sys.argv[3]))))

VK = {'K': 0x4B, 'L': 0x4C, 'I': 0x49, 'J': 0x4A, 'Return': 0x0D, 'Backspace': 0x08, 'Up': 0x26, 'Down': 0x28,
      'Left': 0x25, 'Right': 0x27, 'Q': 0x51, 'E': 0x45, '1': 0x31, '3': 0x33, 'W': 0x57, 'A': 0x41, 'S2': 0x53, 'D2': 0x44, 'F': 0x46, 'H': 0x48, 'T2': 0x54, 'Tab': 0x09, 'G': 0x47, '2': 0x32, '4': 0x34}
KEYOF = dict(X='K', O='L', T='I', S='J', START='Return', SELECT='Backspace', U='Up', D='Down', L='Left', R='Right',
             L1='Q', R1='E', L2='1', R2='3', L3='2', R3='4', RU='T2', RD='G', RL='F', RR='H', LU='W', LD='S2', LL='A', LR='D2')
def _pid():
    r = subprocess.run(['tasklist', '/fi', 'imagename eq pcsx2-24.exe', '/fo', 'csv', '/nh'], capture_output=True, text=True)
    for l in r.stdout.splitlines():
        if l.startswith('"'): return int(l.split('","')[1])
_CB = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
_U = ctypes.windll.user32
_U.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
_U.EnumChildWindows.argtypes = [ctypes.c_void_p, _CB, ctypes.c_void_p]
_HS = []
@_CB
def _child(c, l): _HS.append(c); return True
def _handles():
    del _HS[:]
    for h in wins(_pid()):
        _HS.append(h); _U.EnumChildWindows(ctypes.c_void_p(h), _child, None)
    return list(_HS)
def khold(names, hold=0.5):
    """여러 키 동시 누름. names: 'L1+RR'"""
    hs = _handles()
    vs = [VK[KEYOF.get(n, n)] for n in names.split('+')]
    def m(vk, up):
        sc = _U.MapVirtualKeyW(vk, 0) | (0x100 if vk in (0x25, 0x26, 0x27, 0x28) else 0)
        return 1 | (sc << 16) | ((3 << 30) if up else 0)
    for vk in vs:
        for h in hs: _U.PostMessageW(h, 0x100, vk, m(vk, 0))
        time.sleep(0.05)
    time.sleep(hold)
    for vk in reversed(vs):
        for h in hs: _U.PostMessageW(h, 0x101, vk, m(vk, 1))
    time.sleep(0.3)
def kpress(name, hold=0.12): khold(name, hold)
