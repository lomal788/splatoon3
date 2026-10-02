"""NVN 함수 포인터 슬롯 → 이름 표 (로더 0x710083eb80 판독) 와 디스어셈블 주석.
사용: paintgpu_nvnmap.py annotate <함수주소>   (함수 디스어셈블에 NVN 이름 주석)
      paintgpu_nvnmap.py name <슬롯주소|값주소>"""
import re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
PY = sys.executable

def disasm(args):
    return subprocess.run([PY, str(HERE / "disasm.py")] + args, capture_output=True, text=True, encoding="utf-8").stdout

def build_map():
    txt = disasm(["0x710083eb80", "--end", hex(0x710083eb80 + 14924)])
    m = {}
    name = None
    for line in txt.splitlines():
        s = re.search(r'; "(nvn\w+)"', line)
        if s:
            name = s.group(1); continue
        s = re.search(r'ldr x8, \[x8, #0x[0-9a-f]+\]\s+; \[(0x[0-9a-f]+)\] = u64 (0x[0-9a-f]+)', line)
        if s and name:
            m[int(s.group(1), 16)] = name
            m[int(s.group(2), 16)] = name
            name = None
    return m

def main():
    m = build_map()
    if sys.argv[1] == "name":
        for a in sys.argv[2:]:
            print(a, m.get(int(a, 16)))
        return
    txt = disasm([sys.argv[2], "--func"])
    for line in txt.splitlines():
        for a in re.findall(r'0x7105[0-9a-f]{6}', line):
            if int(a, 16) in m:
                line += f"   <{m[int(a,16)]}>"
                break
        print(line)

if __name__ == "__main__":
    main()
