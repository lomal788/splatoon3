import sys, re
sys.path.insert(0, 'C:/dev/splatoon3/web/tools')
from xref import BASE, load_img
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
m = load_img()
lo = int(sys.argv[1], 16); hi = int(sys.argv[2], 16)
offs = [int(x, 16) for x in sys.argv[3].split(',')]
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
pat = [re.compile(r'#0x%x\]' % o) for o in offs]
addpat = [re.compile(r'^add\s+x\d+, x\d+, #0x%x$' % o) for o in offs]
for a in range(lo, hi, 4):
    w = m[a - BASE:a - BASE + 4]
    for i in md.disasm(w, a):
        s = i.mnemonic + ' ' + i.op_str
        if i.mnemonic.startswith(('st', 'ld')) and any(p.search(s) for p in pat) and 'sp' not in i.op_str.split('[')[1]:
            if len(sys.argv) > 4 and sys.argv[4] == 'st' and not i.mnemonic.startswith('st'):
                continue
            print(hex(a), s)
        elif any(p.match(s) for p in addpat):
            print(hex(a), s)
