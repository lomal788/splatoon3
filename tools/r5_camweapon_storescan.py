"""범위 안에서 [reg, #off] 형태로 off(들)에 쓰는 모든 저장 명령(str/stp/stur, 8/4바이트 겹침 포함)을 찾는다.
사용: r5_camweapon_storescan.py <lo> <hi> <off>  — off 를 덮는 8바이트 str/stp 도 포함"""
import sys, re
from pathlib import Path
import capstone
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img
lo, hi, off = (int(x, 16) for x in sys.argv[1:4])
m = load_img()
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM); md.skipdata = True
pat = re.compile(r"\[(\w+), #(-?0x[0-9a-f]+)\]")
for x in md.disasm(bytes(m[lo - BASE:hi - BASE]), lo):
    if not x.mnemonic.startswith("st"): continue
    mm = pat.search(x.op_str)
    if not mm or mm.group(1) == "sp": continue
    o = int(mm.group(2), 16)
    regs = x.op_str.split("[")[0]
    size = 8 if regs.strip().startswith(("x", "d")) else 4 if regs.strip().startswith(("w", "s")) else 16 if regs.strip().startswith("q") else 1
    if x.mnemonic in ("strb", "sturb"): size = 1
    if x.mnemonic in ("strh", "sturh"): size = 2
    n = 2 if x.mnemonic == "stp" else 1
    if o <= off < o + size * n:
        print(hex(x.address), x.mnemonic, x.op_str)
