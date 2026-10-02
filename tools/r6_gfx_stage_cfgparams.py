"""r6 gfx_stage: gsys 장면 설정 객체(장면+0x1c0) 생성자 0x7103705fec 를 unicorn 으로 실행해
값 오프셋 → 파라미터 이름 해시(CRC32, 생성자가 인라인 계산) 대응을 뽑는다. agl 파라미터 객체 = {+0 vtable, +8 이름 해시, +0x10 다음, +0x18 값}.

- 스텁: 생성자 안의 bl 호출 중 하위 객체 생성 등 10종을 즉시 반환으로 바꾼다(x0 그대로). memset/memcpy 는 SDK 원본(sdk.img)을
  연결해 그대로 실행한다. 이름 문자열 생성 0x7100f93144(FixedSafeString 형식화 → SDK VSNPrintf)는 sdk 내부 가져오기가
  재배치되지 않아 실행할 수 없어 파이썬 C 형식 변환으로 대체한다(스텁, 정수·문자열 인자만).
  이름 해시 계산(crc32b)과 값·해시 기록은 생성자 본문 명령이라 그대로 실행된다. 하위 객체 안 파라미터는 이 표에 없다.
- 인자: x0 = 객체(0 으로 채운 메모리), x1 = 파라미터 목록 헤더(가짜). sdk.img 를 0 번지에 올린다(재배치 전 절대 포인터 기준, 널 역참조도 흡수),
  agl::env 타입 ID 전역 0x7105999160..0x71059991b8 은 작은 번호를 가리키게 둔다(이름 해시와 무관).
- 이름 복원: 생성자 본문의 crc32b 명령을 추적해 사슬별 입력 문자를 모으고, zlib.crc32 로 다시 계산해 해시가 같은 것만 이름으로 쓴다.
- 출력: 값 오프셋, 해시, 이름, 기본값(u32), gsys.bgmsconf Common 덤프 값.
사용: PY web/tools/r6_gfx_stage_cfgparams.py [값오프셋16진 ...] → analysis/r6_gfx_stage/gsys_cfg_params.tsv
"""
import re, struct, sys, zlib
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn.arm64_const import *

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "extracted/exefs/main.reloc.img"
BASE = 0x7100000000
FN, SIZE = 0x7103705fec, 27080
STACK, OBJ, LIST, RET = 0x10000000, 0x20000000, 0x21000000, 0x30000000

img = IMG.read_bytes()
mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
mu.mem_map(BASE, (len(img) + 0xFFFF) & ~0xFFFF); mu.mem_write(BASE, img)
for a, n in ((STACK, 0x100000), (OBJ, 0x100000), (LIST, 0x10000), (RET, 0x1000)):
    mu.mem_map(a, n)
mu.mem_write(RET, struct.pack("<I", 0xD65F03C0))
for i, g in enumerate(range(0x7105999160, 0x71059991c0, 8)):  # agl::env 타입 ID 전역(*g → s16 ID) — 런타임 등록값 대신 작은 번호
    mu.mem_write(LIST + 0x8000 + i * 2, struct.pack("<h", i + 1))
    mu.mem_write(g, struct.pack("<Q", LIST + 0x8000 + i * 2))
mu.reg_write(UC_ARM64_REG_CPACR_EL1, 0x300000)
mu.mem_write(0x7105999ab8, struct.pack("<QI", LIST + 0x9000, 0x40))  # 정적 SafeString(정적 초기화 전 0) — 버퍼만 채움
# SDK 원본 함수 연결: 이름 문자열 생성(0x7100f93144 → nn::util::VSNPrintf), memset/memcpy 는 스텁하지 않고 sdk.img 를 부른다
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_player_libm_emu import symbols
SBASE = 0  # sdk.img 는 재배치 전 이미지라 내부 절대 포인터가 0 기준 → 0 번지에 올린다(널 역참조도 여기서 흡수)
sdk = (ROOT / "extracted/exefs/sdk.img").read_bytes()
mu.mem_map(SBASE, (len(sdk) + 0xFFFF) & ~0xFFFF); mu.mem_write(SBASE, sdk)
ssym = symbols(sdk)
def plt_got(plt):
    a, b = struct.unpack("<II", img[plt - BASE:plt - BASE + 8])
    imm = ((a >> 29) & 3) | (((a >> 5) & 0x7FFFF) << 2)
    return ((plt & ~0xFFF) + (imm << 12)) + ((b >> 10) & 0xFFF) * 8
KEEP = {0x7100f93144}
for plt, nm in ((0x7103e99f10, "memset"), (0x7103e99f20, "memcpy")):
    mu.mem_write(plt_got(plt), struct.pack("<Q", SBASE + ssym[nm][0]))
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
bls = set()
terms = set()  # 정적 SafeString 끝 0 쓰기(sturb wzr,[x,#-1]) — 정적 초기화 안 된 전역이면 건너뜀
o = FN - BASE
for ins in md.disasm(img[o:o + SIZE], FN):
    if ins.mnemonic == "bl" and int(ins.op_str.lstrip("#"), 16) not in KEEP:
        bls.add(ins.address)
    if ins.mnemonic == "sturb" and ins.op_str.startswith("wzr") and ins.op_str.endswith("#-1]"):
        terms.add(ins.address)


def cstr(uc, a):
    out = b""
    while True:
        c = bytes(uc.mem_read(a, 1))
        if c == bytes(1) or len(out) > 200: return out.decode("latin1")
        out += c; a += 1


def fmt_hook(uc, addr, size, ud):
    """0x7100f93144(FixedSafeString<0x40>::format) 대체: 원본과 같은 머리(+8 버퍼 포인터, +0x10 용량 0x40, +0x14 버퍼)를 쓰고
    파이썬 C 형식 변환(%s %d %u %02d 등 정수·문자열만)으로 버퍼를 채운다. 이름 문자열 생성 외 용도 없음."""
    x0 = uc.reg_read(UC_ARM64_REG_X0)
    f = cstr(uc, uc.reg_read(UC_ARM64_REG_X1))
    args = [uc.reg_read(UC_ARM64_REG_X2 + i) for i in range(6)]
    conv = []
    k = 0
    for m in re.finditer(r"%[-0-9]*([sdux])", f):
        v = args[k]; k += 1
        conv.append(cstr(uc, v) if m.group(1) == "s" else (v & 0xFFFFFFFF) if m.group(1) in "ux" else struct.unpack("<i", struct.pack("<I", v & 0xFFFFFFFF))[0])
    txt = (f % tuple(conv)).encode("latin1")[:0x3f]
    uc.mem_write(x0 + 8, struct.pack("<QI", x0 + 0x14, 0x40))
    uc.mem_write(x0 + 0x14, txt + bytes(1))
    uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))


def md_one(a):
    return next(md.disasm(img[a - BASE:a - BASE + 4], a))


mu.hook_add(UC_HOOK_CODE, fmt_hook, None, 0x7100f93144, 0x7100f93148)


CRC = {}  # crc32b 사슬 추적: 중간 crc 값 → 지금까지 넣은 문자열 (생성자가 인라인으로 계산하는 이름 복원)
crcs = {}
for ins in md.disasm(img[o:o + SIZE], FN):
    if ins.mnemonic == "crc32b":
        r = [int(x.strip()[1:]) for x in ins.op_str.split(",")]
        crcs[ins.address] = r


def crc_pre(uc, addr):
    d, n, m = crcs[addr]
    nv = uc.reg_read(UC_ARM64_REG_X0 + n) & 0xFFFFFFFF
    mv = uc.reg_read(UC_ARM64_REG_X0 + m) & 0xFF
    pend.append((d, (CRC.get(nv, "") if nv != 0xFFFFFFFF else "") + chr(mv)))


pend = []


def hook(uc, addr, size, ud):
    while pend:
        d, st = pend.pop()
        CRC[uc.reg_read(UC_ARM64_REG_X0 + d) & 0xFFFFFFFF] = st
    if addr in crcs:
        crc_pre(uc, addr)
    if addr in terms:
        rn = int(md_one(addr).op_str.split("[")[1].split(",")[0][1:])
        if uc.reg_read(UC_ARM64_REG_X0 + rn) < 0x1000:
            uc.reg_write(UC_ARM64_REG_PC, addr + 4)
        return
    if addr in bls:
        uc.reg_write(UC_ARM64_REG_PC, addr + 4)


mu.hook_add(UC_HOOK_CODE, hook, None, FN, FN + SIZE)
mu.hook_add(UC_HOOK_MEM_UNMAPPED, lambda uc, a, ad, s, v, u: print("unmapped", hex(ad), hex(uc.reg_read(UC_ARM64_REG_PC))) or False)
mu.reg_write(UC_ARM64_REG_X0, OBJ); mu.reg_write(UC_ARM64_REG_X1, LIST)
mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000); mu.reg_write(UC_ARM64_REG_LR, RET)
try:
    mu.emu_start(FN, RET, count=5_000_000)
except Exception as e:
    pc = mu.reg_read(UC_ARM64_REG_PC); print("# 실행 중단(그 앞까지 기록된 파라미터만 유효)", e, hex(pc))
else:
    pc = None; print("# 생성자 끝까지 실행")

names = {}
for line in (ROOT / "analysis/gfx4/aamp_names.txt").read_text(encoding="utf-8").split():
    names[zlib.crc32(line.encode())] = line
for extra in ("depth_shadow_polygon_offset", "depth_shadow_polygon_scale"):  # 생성자 실행 구간 밖 해시 — 후보 이름 사전 대조로 찾은 것
    names[zlib.crc32(extra.encode())] = extra
for v, st in CRC.items():  # 생성자 실행 중 복원한 이름(검증: zlib.crc32 와 같은 것만)
    if zlib.crc32(st.encode("latin1")) == (~v & 0xFFFFFFFF):
        names[~v & 0xFFFFFFFF] = st
dump = {}
for line in (ROOT / "analysis/gfx4/gsys_bgmsconf_common.txt").read_text(encoding="utf-8").splitlines():
    m = re.match(r"\s+(\S+) : (\w+) = (.*)", line)
    if m:
        k = m.group(1)
        h = int(k, 16) if k.startswith("0x") else zlib.crc32(k.encode())
        dump[h] = (k, m.group(2), m.group(3))
obj = bytes(mu.mem_read(OBJ, 0x2000))
rows = ["val_off\thash\tname\tdefault_u32\tCommon"]
want = [int(x, 16) for x in sys.argv[1:]]
for p in range(0x8, 0x2000 - 0x18, 8):
    h = struct.unpack_from("<I", obj, p + 8)[0]
    if h == 0 or h not in dump and h not in names:
        continue
    val = p + 0x18
    d = struct.unpack_from("<I", obj, val)[0]
    nm = names.get(h, dump.get(h, ("?",))[0])
    c = dump.get(h)
    rows.append(f"{val:#x}\t{h:#010x}\t{nm}\t{d:#x}\t{(c[1] + ' ' + c[2]) if c else ''}")
txt = "\n".join(rows)
(ROOT / "analysis/r6_gfx_stage/gsys_cfg_params.tsv").write_text(txt + "\n", encoding="utf-8")
for r in rows:
    if not want or any(r.startswith(f"{w:#x}\t") for w in want):
        print(r)
