"""멤버 선언식 UBO(엔진 '멤버 객체 + 레이아웃 커서' 방식)의 레이아웃을 원본 코드 실행으로 뽑는다.

동작: 생성자(ctor)를 unicorn 으로 실행 → 멤버 목록(+list_off 이중 연결 리스트, 노드 = 멤버+0x10)을 생성 순서로 따라가며
각 멤버 vtable 슬롯 2(선언 함수, vt+0x10)를 가짜 UBO 객체로 호출 → 형식 표(12 B: u32 count, u16 offset, u16 comps, u8 kind)와
커서(+0x38)를 읽어 멤버별 바이트 오프셋을 얻는다. 초기값은 멤버+0x38 부터 16 B.

사용: PY web/tools/render_ubo_layout.py [ctor 주소] [하위객체→목록 오프셋] [출력 tsv]
  기본값 = SceneCommonUBOHolder 하위 객체(holder+0x2b0) ctor 0x71011823d0, 목록 +0x2b0
  BL 대상 중 하위 초기화 함수는 즉시 반환으로 스텁(STUBS).
"""
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / 'extracted' / 'exefs' / 'main.reloc.img'
BASE = 0x7100000000
STACK, OBJ, AUX, RET = 0x10000000, 0x20000000, 0x21000000, 0x30000000

ctor = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x71011823d0
list_off = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x2b0
out = sys.argv[3] if len(sys.argv) > 3 else None
STUBS = {0x7103585094}  # 하위 객체 초기화(뮤텍스류) — 레이아웃과 무관

img = IMG.read_bytes()
mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF)
mu.mem_write(BASE, img)
for a, n in ((STACK, 0x100000), (OBJ, 0x100000), (AUX, 0x100000), (RET, 0x1000)):
    mu.mem_map(a, n)
mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
mu.mem_write(RET, struct.pack('<I', 0xD65F03C0))


def hook(uc, addr, size, ud):
    if addr in STUBS:
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))


mu.hook_add(UC_HOOK_CODE, hook)


def call(fn, *args):
    for i, a in enumerate(args):
        mu.reg_write(UC_ARM64_REG_X0 + i, a)
    mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
    mu.reg_write(UC_ARM64_REG_X30, RET)
    mu.emu_start(fn, RET, count=2_000_000)


q = lambda a: struct.unpack('<Q', mu.mem_read(a, 8))[0]
call(ctor, OBJ)
head = OBJ + list_off
node_off = struct.unpack('<i', mu.mem_read(OBJ + list_off + 0x14, 4))[0]  # +0x2c4 = 노드 오프셋(0x10)
members = []
node = q(head + 8)
while node != head and len(members) < 512:
    m = node - node_off
    members.append(m)
    node = q(node + 8)

# 가짜 UBO: +0x10 → 표 헤더 {u64 표, u16 총수, u16 현재수}, +0x38 커서
ubo, hdr, tbl = AUX, AUX + 0x100, AUX + 0x1000
mu.mem_write(ubo, b'\0' * 0x100)
mu.mem_write(hdr, struct.pack('<QHH', tbl, len(members), 0))
mu.mem_write(ubo + 0x10, struct.pack('<Q', hdr))
rows = []
for k, m in enumerate(members):
    vt = q(m)
    decl = q(vt + 0x10)
    before = struct.unpack('<I', mu.mem_read(ubo + 0x38, 4))[0]
    call(decl, m, ubo)
    cur = struct.unpack('<H', mu.mem_read(hdr + 0xa, 2))[0]
    idx = struct.unpack('<i', mu.mem_read(m + 8, 4))[0]
    cnt, off, comps, kind = struct.unpack('<IHHB', mu.mem_read(tbl + (cur - 1) * 12, 9))
    after = struct.unpack('<I', mu.mem_read(ubo + 0x38, 4))[0]
    val = struct.unpack('<4f', mu.mem_read(m + 0x38, 16))
    rows.append((k, idx, m - OBJ, vt, decl, kind, comps, cnt, off, after, val))
end = struct.unpack('<I', mu.mem_read(ubo + 0x38, 4))[0]
lines = ['order\tindex\tmember_off\tvtable\tdeclare\tkind\tcomps\tcount\tubo_off\tvec4[i].c\tcursor_after\tinit']
for k, idx, mo, vt, decl, kind, comps, cnt, off, after, val in rows:
    lines.append('%d\t%d\t0x%x\t0x%x\t0x%x\t%d\t%d\t%d\t0x%x\t[%d].%s\t0x%x\t%s' % (
        k, idx, mo, vt, decl, kind, comps, cnt, off, off // 16, 'xyzw'[(off % 16) // 4], after,
        ','.join('%g' % v for v in val)))
lines.append('# members %d, final cursor 0x%x (%d B)' % (len(rows), end, end))
text = '\n'.join(lines)
print(text)
if out:
    Path(out).write_text(text + '\n', encoding='utf-8')
