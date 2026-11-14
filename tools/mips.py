import struct
from capstone import *
E=open(r'D:\ps2\24_더게임\work\SLUS_212.68','rb').read()
def v2o(a):
    if 0x100000<=a<0x593860: return a-0x100000+0x80
    if 0x597880<=a<0x597880+0x63ecc: return a-0x597880+0x493900
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS64+CS_MODE_LITTLE_ENDIAN)
def dis(a,n=40):
    o=v2o(a); out=[]
    for i in range(n):
        w=E[o+i*4:o+i*4+4]
        ins=list(md.disasm(w,a+i*4))
        out.append('%08x: %s %s'%(a+i*4,ins[0].mnemonic,ins[0].op_str) if ins else '%08x: .word %s'%(a+i*4,w.hex()))
    return '\n'.join(out)
def words():
    for o in range(0x80,0x80+0x493860,4): yield o-0x80+0x100000, struct.unpack_from('<I',E,o)[0]
