"""GOT 경유 전역 포인터에 쓰는 명령 찾기: ldr xA,[xB,#got_lo] 뒤 몇 명령 안 str xR,[xA(,#off)]."""
import sys
from pathlib import Path
import capstone
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, load_img
import subprocess

def main():
    got = int(sys.argv[1], 16)
    off = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0
    out = subprocess.run([sys.executable, str(Path(__file__).parent / "xref.py"), "addr", hex(got)], capture_output=True, text=True).stdout
    refs = [int(t.rstrip("L"), 16) for t in out.split(":", 1)[1].split()]
    m = load_img()
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    md.detail = True
    for r in refs:
        code = bytes(m[r - BASE: r - BASE + 4 * 12])
        insns = list(md.disasm(code, r))
        if not insns: continue
        i0 = insns[0]
        if not i0.mnemonic.startswith("ldr"): continue
        reg = i0.op_str.split(",")[0]
        ptr = None
        for ins in insns[1:]:
            ops = ins.op_str
            if ins.mnemonic == "ldr" and f"[{reg}]" in ops and ops.startswith("x"):
                ptr = ops.split(",")[0]
                continue
            if ins.mnemonic in ("str", "stp") and (f"[{reg}]" in ops):
                print(hex(ins.address), ins.mnemonic, ops, "(전역 자체에 씀)")
            if ptr and ins.mnemonic.startswith("st") and f"[{ptr}, #{hex(off)}]" in ops:
                print(hex(ins.address), ins.mnemonic, ops, f"(*전역+{hex(off)})")
            if ins.mnemonic in ("ret", "b", "bl", "br", "blr"): break

main()
