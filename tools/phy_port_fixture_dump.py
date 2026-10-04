"""[physics port] 원본 실행 하네스의 입력·원본 출력을 웹 비트 대조 fixture 로 저장한다.

기존 하네스(r8 solver/contact, r6 write-back/정렬/필터/하위 레이어, r6 paint 발밑 모니터)를 소스 그대로 실행하되
(1) 사례 수를 줄이고 (2) 모든 사례의 입력·원본 출력을 기록하도록 기록 조건만 바꾼다. 원본 함수 실행·스텁 경계는 각 하네스와 같다.
각 하네스는 원본 출력과 독립 재구현이 비트 일치함을 스스로 assert 하므로, 여기 저장되는 출력은 원본 실행값이다.

실행: cd C:/dev/splatoon3 && .venv/Scripts/python web/tools/phy_port_fixture_dump.py
출력: web/games/splatoon3/tests/fixtures/phy_native.json, phy_game.json
"""
import copy
import json
import math
import struct
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
sys.path.insert(0, str(TOOLS))
OUT = ROOT / "web/games/splatoon3/tests/fixtures"
TMP = Path(tempfile.mkdtemp(prefix="phy_port_"))


def jfix(o):
    """numpy·튜플 → JSON. NaN/inf 는 f32 비트 문자열로."""
    if isinstance(o, dict):
        return {str(k): jfix(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jfix(v) for v in o]
    if hasattr(o, "item") and not isinstance(o, (bytes, str)):
        o = o.item()
    if isinstance(o, float):
        if math.isnan(o) or math.isinf(o):
            return "f32:" + struct.pack("<f", o).hex()
        return o
    return o


def run_script(name, patches, count_patch=None):
    src = (TOOLS / name).read_text(encoding="utf-8")
    for a, b in patches:
        if a not in src:
            raise SystemExit(f"{name}: 패치 대상 없음: {a[:60]}")
        src = src.replace(a, b)
    ns = {"__name__": "phy_port", "__file__": str(TOOLS / name), "OUTDIR": str(TMP) + "/"}
    exec(compile(src, str(TOOLS / name), "exec"), ns)
    return ns


def r8_path(src_name):
    return (f"Path('analysis/completion/r8/{src_name}')", f"Path(OUTDIR+'{src_name}')")


native = {}

# --- 접촉 행 보정(target/old/carry) 0a16d78..0a16e24 ---
ns = run_script("r8_camweapon_contact_bias_block_emu.py", [
    ("for k in range(1024):", "for k in range(64):"),
    ("for n in range(4097):", "for n in range(513):"),
    (" if n<6:fixtures.append(", " if True:fixtures.append("),
    r8_path("contact_bias_block_emu.json"),
])
native["bias"] = {"threshold": ns["threshold"], "dt": ns["dt"], "k": ns["k"], "c0": ns["c0"], "gamma": ns["gamma"], "ratio": ns["ratio"],
                  "cases": ns["fixtures"]}

# --- 단일 몸체 법선 충격량 0a1a98c..0a1abd0 ---
ns = run_script("r8_camweapon_contact_normal_block_emu.py", [
    ("for k in range(4097):", "for k in range(513):"),
    (" if k<4:fixtures.append(", " if True:fixtures.append("),
    r8_path("contact_normal_block_emu.json"),
])
native["normal"] = ns["fixtures"]

# --- 여러 행 순차 법선 반복 0a18d8c..0a1911c (두 몸체 경로) ---
ns = run_script("r8_camweapon_contact_multi_normal_loop_emu.py", [
    ("for n in range(1025):", "for n in range(257):"),
    (" if n<4:fixtures.append(dict(count=count,", " if True:fixtures.append(dict(WA=WA,WB=WB,IA=IA,IB=IB,count=count,"),
    r8_path("contact_multi_normal_loop_emu.json"),
])
native["multi"] = ns["fixtures"]

# --- carry 0a4b514 (상한 100/200 포함) ---
ns = run_script("r8_physics_prestep_cap_emu.py", [
    ("for i in range(2048):", "for i in range(512):"),
    (" if i<4:samples.append(dict(i=i,", " if True:samples.append(dict(i=i,cap=float(cap),"),
    r8_path("physics_prestep_cap_emu.json"),
])
native["prestep"] = {"tau": float(ns["tau"]), "g": [float(x) for x in ns["g"]], "cases": ns["samples"]}

# --- finalize 0a4b8c8 (상한 100/200 포함) ---
ns = run_script("r8_physics_finalizer_cap_emu.py", [
    ("for i in range(2048):", "for i in range(512):"),
    (" if i<4:samples.append(dict(i=i,", " if True:samples.append(dict(i=i,cap=float(cap),old=list(old),"),
    r8_path("physics_finalizer_cap_emu.json"),
])
native["finalize"] = {"dt": float(ns["dt"]), "tau": float(ns["tau"]), "invsub": float(ns["invsub"]), "invtau": float(ns["invtau"]),
                      "cases": ns["samples"]}

# --- COM → 몸체 원점 09d5b68 ---
ns = run_script("r8_physics_pose_emu.py", [
    ("for i in range(1024):", "for i in range(512):"),
    (" if i<4:samples.append(", " if True:samples.append("),
    r8_path("physics_pose_emu.json"),
])
native["pose"] = ns["samples"]

# --- 초기 current/baseline 09d4ba8 ---
ns = run_script("r8_physics_initial_velocity_emu.py", [
    ("for i in range(1024):", "for i in range(256):"),
    (" if i<3:samples.append(dict(i=i,", " if True:samples.append(dict(i=i,gs=[float(x) for x in gs],"),
    r8_path("physics_initial_velocity_emu.json"),
])
native["initial"] = ns["samples"]

# --- game stage → native 선속도 setter (3c50c7c → 09d9e54) ---
ns = run_script("r8_physics_native_velocity_emu.py", [
    (" if i<4 or i>=1000:traces.append(dict(i=i,flags=[linflag,angflag],",
     " if i%3==0 or i>=1000:traces.append(dict(i=i,old=[struct.unpack('<I',struct.pack('<f',float(x)))[0] for x in old],v=[struct.unpack('<I',struct.pack('<f',float(x)))[0] for x in v],got=list(struct.unpack('<3I',got)),flags=[linflag,angflag],"),
    r8_path("physics_native_velocity_emu.json"),
])
native["velocity"] = {"cap": 100.0, "cases": [{k: t[k] for k in ("old", "v", "got", "flags")} for t in ns["traces"]]}

# --- solverInfo 0a452fc → 0a4536c ---
ns = run_script("r8_combat_solver_info_emu.py", [
    ("for i in range(1024):", "for i in range(64):"),
    (" if i<4:samples.append(dict(i=i,", " if True:samples.append(dict(i=i,raw=list(struct.unpack('<64I',bytes(u.mu.mem_read(p,0x100)))),"),
    r8_path("solver_info_emu.json"),
    ("print(json.dumps({**out,'mismatch':bad[:4]},ensure_ascii=False));", ""),
])
native["solver_info"] = ns["samples"]

(OUT / "phy_native.json").write_text(json.dumps(jfix(native), separators=(",", ":")) + "\n", encoding="utf-8")
print("phy_native.json", {k: (len(v) if isinstance(v, list) else len(v.get("cases", []))) for k, v in native.items()})

game = {}

# --- 평상시 write-back 0x71024d26f8 (본체+0x10 = 몸체 원점 − r·up) ---
ns = run_script("r6_physics_writeback_emu.py", [
    ("        if ci < 4:", "        if True:"),
    ('ROOT / "analysis/completion/r6/', 'Path(OUTDIR) / "'),
])
wb = ns["run"](cases=256)
game["writeback"] = [{k: s[k] for k in ("r", "S210", "fa0", "body_t", "up", "actor28c", "hon10")} for s in wb["samples"]]

# --- 접촉 목록 정렬 0x7103a6144c (모드 3 힙 정렬) ---
ns = run_script("r6_physics_contactsort_emu.py", [
    ("        if ci < 3:", "        if True:"),
    ('ROOT / "analysis/completion/r6/', 'Path(OUTDIR) / "'),
])
cs = ns["run"](cases=512)
game["contactsort"] = [{k: s[k] for k in ("n", "cap", "keys_in", "original")} for s in cs["samples"]]

# --- 형상 행 + 공통 쌍 필터 결합 0x7103c5e244 ---
ns = run_script("r6_physics_shapefilter_emu.py", [
    ("        if ci < 6:", "        if True:"),
    ('row = {"case": ci, "A":', 'row = {"case": ci, "full": copy.deepcopy(st), "tblA": tbl[0][a["L"]], "tblB": tbl[0][b_["L"]], "A":'),
    ('ROOT / "analysis/completion/r6/', 'Path(OUTDIR) / "'),
    ("import json\n", "import json\nimport copy\n"),
])
sf = ns["run"](cases=512)
rows = []
for s in sf["samples"]:
    ent = {"tblA": s["tblA"], "tblB": s["tblB"], "original": s["original"]}
    for nm in ("A", "B"):
        x = s["full"][nm]
        row = None
        if x["key"] != -1 and (x["tag"] & 0x1FFF) < x["count"]:
            row = x["rows"][x["tag"] & 0x1FFF]
        ent[nm] = {"L": x["L"], "S": x["S"], "bit28": x["bit28"], "m18": x["m18"], "m1c": x["m1c"], "compound": x["compound"],
                   "cb8": x["cb8"], "cbc": x["cbc"], "row": row}
    rows.append(ent)
game["shapefilter"] = rows

# --- 플레이어 몸체 하위 레이어 0x71024f5fc4~0x71024f60f8 ---
ns = run_script("r6_physics_sublayer_emu.py", [
    ("        if ci < 5:", "        if True:"),
    ('ROOT / "analysis/completion/r6/', 'Path(OUTDIR) / "'),
])
sl = ns["run"](cases=512)
game["sublayer"] = [{k: s[k] for k in ("sp", "a7b9", "t", "zombie_eec", "dokan30", "flag", "original")} for s in sl["samples"]]

# --- 발밑 모니터 델리게이트 0x7102c5ec74 · 가중치 0x7102c71330 ---
ns = run_script("r6_paint_footmon_emu.py", [
    ("N = 4000", "N = 512"),
    ("        # A) 델리게이트: x0 = O+0x48, x8 = out", "        SNAP_A = copy.deepcopy(Rm)\n        # A) 델리게이트: x0 = O+0x48, x8 = out"),
    ("        ok_a += good", "        ok_a += good; REC_A.append(dict(r=SNAP_A, got=got, got_valid=got_valid))"),
    ("        before = len(rel_calls)", "        SNAP_B = [dict(act=int(e['act']), cnt=e['cnt'], w=float(e['w']), reg=int(e['reg']), mon_has=int(e['mon_has'])) for e in ents]\n        before = len(rel_calls)"),
    ("        ok_b += goodb", "        ok_b += goodb; REC_B.append(dict(rate=float(rate), frames=frames, ents=SNAP_B, got=gb, released=len(rel_calls) - before))"),
    ('(ROOT / "analysis/paint/r6_footmon_emu_out.json")', '(Path(OUTDIR) / "footmon.json")'),
    ("import json, random, struct, sys\n", "import json, random, struct, sys, copy\nREC_A = []\nREC_B = []\n"),
])
ns["main"]()
game["footmon_delegate"] = ns["REC_A"]
game["footmon_weight"] = ns["REC_B"]

(OUT / "phy_game.json").write_text(json.dumps(jfix(game), separators=(",", ":")) + "\n", encoding="utf-8")
print("phy_game.json", {k: len(v) for k, v in game.items()})
