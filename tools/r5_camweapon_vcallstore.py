"""가상 호출 vt+OFF 결과(x0)를 몇 명령 안 [xN,#STOFF]에 저장하는 위치 스캔."""
import sys
from pathlib import Path
import capstone
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xref import BASE, TEXT_END, load_img
voff, stoff = int(sys.argv[1], 16), int(sys.argv[2], 16)
lo = int(sys.argv[3], 16) if len(sys.argv) > 3 else BASE
hi = int(sys.argv[4], 16) if len(sys.argv) > 4 else BASE + TEXT_END
m = load_img()
md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
md.skipdata = True
code = bytes(m[lo - BASE:hi - BASE])
ins = list(md.disasm(code, lo))
for i, x in enumerate(ins):
    if x.mnemonic == "ldr" and x.op_str.endswith(f", #{hex(voff)}]") and x.op_str.startswith("x"):
        r = x.op_str.split(",")[0]
        for j in range(i + 1, min(i + 5, len(ins))):
            if ins[j].mnemonic == "blr" and ins[j].op_str == r:
                for k in range(j + 1, min(j + 8, len(ins))):
                    if ins[k].mnemonic.startswith("st") and ins[k].op_str.startswith("x0,") and ins[k].op_str.endswith(f"#{hex(stoff)}]"):
                        print(hex(x.address), hex(ins[k].address), ins[k].op_str)
                break
