"""r11 gfx-char: run original v0 functions and save full case inputs/outputs for the web bit tests.

Sections (each the original instructions under unicorn; stubs are listed per section in the output):
  tank      0x71026fb6d0 whole (ordinary tank) + static init constants 0x71058c7118..0x71058c7128
  head      0x71026e613c hat ManualBindSRT composite (same harness shape as completion_head_matrix_emu.py)
  teamRandom 0x7101179d64..0x7101179da0 inline sead::Random draw of 0x7101179c80
  hairArrange 0x71026df700 (r6 harness objects, sinf/cosf python f32 stub)
  clipName  0x710244d0b0 (r5 harness objects, binder lookup stub)
  lod       0x7103788760 selector, distance mode, internal storage
  curves    0x710088e380 float reader on actual Tnk_Simple Gauge/InkShortage curves
Usage: PY web/tools/r11_gfx_char_emu.py → web/games/splatoon3/tests/fixtures/r11_gfx_char_native.json
"""
import json
import math
import random
import struct
import sys
import hashlib
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import (UC_ARM64_REG_LR, UC_ARM64_REG_PC, UC_ARM64_REG_X0, UC_ARM64_REG_X1,
                                 UC_ARM64_REG_X2, UC_ARM64_REG_X3, UC_ARM64_REG_S0, UC_ARM64_REG_X19,
                                 UC_ARM64_REG_W0, UC_ARM64_REG_SP)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC  # noqa: E402
from network_uc import STUB, END, STACK  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "web/games/splatoon3/tests/fixtures/r11_gfx_char_native.json"
f32 = lambda x: struct.unpack("<f", struct.pack("<f", x))[0]
fb = lambda x: struct.unpack("<I", struct.pack("<f", x))[0]
bf = lambda b: struct.unpack("<f", struct.pack("<I", b & 0xFFFFFFFF))[0]
FAKE = 0x40000000


def fake_region(u):
    u.mu.mem_map(FAKE, 0x1000)
    u.mu.mem_write(FAKE, struct.pack("<I", 0xD65F03C0) * 0x400)


# --------------------------------------------------------------------------- tank
def tank_section():
    u = GUC()
    fake_region(u)
    m = u.mu
    # static init writes the .bss constants; read them back (no value assumed)
    init_ok = True
    try:
        u.call(0x71026F5020)
    except Exception as e:  # noqa: BLE001
        init_ok = str(e)
    consts = {"followUp": u.ru32(0x71058C7118), "followDown": u.ru32(0x71058C711C),
              "lockStep": u.ru32(0x71058C7120), "emptyFrames": u.ru32(0x71058C7128)}
    rec = []
    hooks = {}

    def hk(mu, addr, size, d):
        kind = hooks.get(addr)
        if kind is None:
            return
        if kind[0] == "frame":
            rec.append(["frame", kind[1], mu.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF])
        elif kind[0] == "request":
            name = u._cstr(u.rq(mu.reg_read(UC_ARM64_REG_X1))).decode()
            rec.append(["request", name, mu.reg_read(UC_ARM64_REG_X2) & 0xFF])
        elif kind[0] == "stop":
            rec.append(["stop", mu.reg_read(UC_ARM64_REG_X1) & 0xFF])
        elif kind[0] == "xlink":  # x8 = indirect result, x0 = xlink object, x1 = &name
            name = u._cstr(u.rq(mu.reg_read(UC_ARM64_REG_X1))).decode()
            rec.append(["xlink", name])
        elif kind[0] == "update":
            pass
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))

    for a, k in [(0x710399EC94, ("update",)), (0x710399E340, ("request",)), (0x710399F41C, ("stop",))]:
        hooks[a] = k
        m.hook_add(UC_HOOK_CODE, hk, begin=a, end=a)
    tank = u.alloc(0x1900)
    AS = u.alloc(0x80)
    P = u.alloc(0x48 * 5)
    u.u32(AS + 0x18, 5)
    u.wq(AS + 0x20, P)
    for k in range(5):
        slot = u.alloc(0x100)
        l6 = u.alloc(0xa0)
        node = u.alloc(0x10)
        vt = u.alloc(0x40)
        h = FAKE + 0x100 + 8 * k
        hooks[h] = ("frame", k)
        m.hook_add(UC_HOOK_CODE, hk, begin=h, end=h)
        u.wq(vt + 0x28, h)
        u.wq(node, vt)
        u.wq(l6 + 8, node)
        u.wq(l6 + 0x58, node)
        u.wq(slot + 0x58, l6)
        u.wq(P + 0x48 * k, slot)
    xl = u.alloc(0x10)
    xvt = u.alloc(0x40)
    hooks[FAKE + 0x200] = ("xlink",)
    hooks[FAKE + 0x208] = ("xlink",)
    for a in (FAKE + 0x200, FAKE + 0x208):
        m.hook_add(UC_HOOK_CODE, hk, begin=a, end=a)
    u.wq(xvt + 0x10, FAKE + 0x208)
    u.wq(xvt + 0x18, FAKE + 0x200)
    u.wq(xl, xvt)
    rng = random.Random(0x26FB6D0)
    seqs = []
    for s in range(48):
        m.mem_write(tank, b"\0" * 0x1900)
        m.mem_write(tank + 0x538, b"\x01")
        u.wq(tank + 0x18D8, AS)
        u.wq(tank + 0x18D0, xl)
        for off in (0x510, 0x512, 0x514, 0x518, 0x51A, 0x51C, 0x188C, 0x188E):
            m.mem_write(tank + off, struct.pack("<h", -1))
        p6 = 1 if s % 6 else 0
        frames = []
        rem = f32(rng.uniform(0.3, 1.0))
        for fidx in range(90):
            ev = rng.random()
            if ev < 0.12:
                rem = f32(max(0.0, rem - rng.uniform(0.0, 0.3)))
            elif ev < 0.4:
                rem = f32(min(1.0, rem + rng.uniform(0.0, 0.05)))
            if s % 7 == 3 and fidx < 3:
                rem = f32([0.0, 1.0, 0.5][fidx])
            lock = f32(rng.choice([rem, rng.uniform(0, 1.1), 1.0]))
            sub = f32(rng.choice([0.0, 0.0, rng.uniform(0, 0.8)]))
            lack = rng.random() < (0.08 if s % 4 else 0.25)
            sublack = rng.random() < 0.03
            if lack:
                u.u32(tank + 0x4C0, max(struct.unpack("<i", m.mem_read(tank + 0x4C0, 4))[0], 60))
            if sublack:
                u.u32(tank + 0x4C4, max(struct.unpack("<i", m.mem_read(tank + 0x4C4, 4))[0], rng.choice([30, 60, 61])))
            rec.clear()
            u.call(0x71026FB6D0, tank, 0, p6, 0, 0, 0, fargs=(sub, rem, lock))
            assert m.reg_read(UC_ARM64_REG_PC) == END
            st = {"r": u.ru32(tank + 0x520), "lock": u.ru32(tank + 0x524), "sub": u.ru32(tank + 0x528),
                  "c": m.mem_read(tank + 0x52C, 1)[0], "d": m.mem_read(tank + 0x52D, 1)[0],
                  "t0": struct.unpack("<i", m.mem_read(tank + 0x4C0, 4))[0], "t4": struct.unpack("<i", m.mem_read(tank + 0x4C4, 4))[0]}
            frames.append({"in": [fb(sub), fb(rem), fb(lock)], "lack": lack, "sublack": sublack, "calls": list(rec), "state": st})
            # slot 18 0x71026f8280 timer decrement [판독], applied between frames
            for off in (0x4C0, 0x4C4):
                v = struct.unpack("<i", m.mem_read(tank + off, 4))[0]
                u.u32(tank + off, (max(v, 1) - 1) & 0xFFFFFFFF)
            m.mem_write(tank + 0x534, struct.pack("<f", sub))
        seqs.append({"shortageEnabled": bool(p6), "frames": frames})
    return {"function": "0x71026fb6d0", "constants": consts, "staticInit": init_ok, "sequences": seqs,
            "stubs": ["AS update 0x710399ec94 / request 0x710399e340 / stop 0x710399f41c: recorded and returned",
                      "slot frame setters (slot k vt+0x28): recorded S0",
                      "xlink vt+0x10/+0x18: recorded name",
                      "between frames: +0x4c0/+0x4c4 = max(x,1)-1 (slot18 0x71026f8280 [판독]) and +0x534 = subCost (caller)"],
            "pltStubbed": sorted(set(u.plt_stubbed))}


# --------------------------------------------------------------------------- head
def head_section():
    import ctypes
    u = GUC()
    m = u.mu
    head = u.alloc(0x500); owner = u.alloc(0x400); vt = u.alloc(0x240); body = u.alloc(0x80)
    arr = u.alloc(8); ref = u.alloc(8); bone = u.alloc(16); bvt = u.alloc(0x100); target = u.alloc(0x400); inp = u.alloc(0x40)
    u.wq(head + 0x10, owner); u.wq(owner, vt); u.wq(vt + 0x1F8, STUB + 0x504)
    u.wq(head + 0x110, body); u.wq(body + 0x40, arr); u.wq(arr, ref); u.wq(ref, bone); u.wq(bone, bvt); u.wq(bvt + 0x78, STUB + 0x500)
    u.wq(head + 0x3F0, target)
    m.mem_write(head + 0x3BC, b"\xff" * 16)
    st = {}
    pack = lambda a: struct.pack("<12f", *a)

    def hook(mu, addr, size, data):
        if addr == STUB + 0x500:
            mu.mem_write(mu.reg_read(UC_ARM64_REG_X1), pack(st["B"]))
    m.hook_add(UC_HOOK_CODE, hook, begin=STUB + 0x500, end=STUB + 0x504)
    rng = random.Random(0x11E613C)
    I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]
    cases = [([0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0], I)]
    for i in range(160):
        B = [f32(rng.uniform(-8, 8)) for _ in range(12)]
        S = [f32(rng.uniform(-4, 4)) for _ in range(12)]
        if i % 5 == 0:
            S = [f32(v) for v in [1, 0, 0, rng.uniform(-.1, .1), 0, 1, 0, rng.uniform(-.1, .1), 0, 0, 1, rng.uniform(-.1, .1)]]
        cases.append((B, S))
    out = []
    for B, S in cases:
        st["B"] = B
        m.mem_write(head + 0x380, pack(S)); m.mem_write(inp, pack(I)); m.mem_write(target + 0x280, b"\xa4")
        u.call(0x71026E613C, head, inp)
        out.append({"B": [fb(v) for v in B], "S": [fb(v) for v in S], "O": list(struct.unpack("<12I", bytes(m.mem_read(target + 0x238, 48))))})
    return {"function": "0x71026e613c", "cases": out, "stubs": ["owner vt+0x1f8 ret", "body bone vt+0x78 supplies B"]}


# --------------------------------------------------------------------------- team random
def team_section():
    u = GUC()
    m = u.mu
    holder = u.rq(0x71057906A0)  # GOT → global holding the sead::Random pointer (*0x7105997950)
    state_ptr = u.alloc(0x10)
    u.wq(holder, state_ptr)
    rng = random.Random(0x1179C80)
    out = []
    for i in range(400):
        s = [rng.getrandbits(32) for _ in range(4)]
        if i < 4:
            s = [[1, 2, 3, 4], [0, 0, 0, 1], [0xFFFFFFFF] * 4, [0x12345678, 0x9ABCDEF0, 0x0F0F0F0F, 0xF0F0F0F0]][i]
        n = [10, 1, 36, 7, 0x7FFFFFFF][i % 5]
        m.mem_write(state_ptr, struct.pack("<4I", *s))
        u.mu.reg_write(UC_ARM64_REG_X0, n)
        u.mu.reg_write(UC_ARM64_REG_SP, STACK + 0xF0000)
        m.emu_start(0x7101179D6C, 0x7101179DA0)
        idx = m.reg_read(UC_ARM64_REG_X19) & 0xFFFFFFFF
        ns = list(struct.unpack("<4I", m.mem_read(state_ptr, 16)))
        out.append({"state": s, "n": n, "index": idx, "next": ns})
    return {"range": "0x7101179d6c..0x7101179da0 (inside 0x7101179c80)", "statePointer": hex(state_ptr), "cases": out,
            "note": "w0 = matching row count (positive path), global sead::Random state from [0x71057906a0]"}


# --------------------------------------------------------------------------- hair arrange
def hair_section():
    import r6_gfx_char_hairarrange_emu as H
    u = H.HUC()
    u.libm = []
    m = u.mu
    m.mem_map(H.FAKE, 0x1000)
    m.mem_write(H.FAKE, struct.pack("<I", 0xD65F03C0) * 0x400)
    vt = u.alloc(0x200)
    for off in range(0, 0x200, 8):
        u.wq(vt + off, H.FAKE + off)
    bone_names = ["Hair_1_L", "ScalerA", "ScalerB", "Knot_1", "Front_1"]
    st = {"bind": {}, "set": []}

    def hk(mu, addr, size, d):
        off = addr - H.FAKE
        x1, x2, x3 = (mu.reg_read(r) for r in (UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3))
        ret = 0
        if off == 0x40:
            nm = u._cstr(u.rq(x1)).decode()
            ret = bone_names.index(nm) if nm in bone_names else 0xFFFFFFFF
        elif off == 0x68:
            Bm, Sc = st["bind"][x3 & 0xFFFF]
            mu.mem_write(x1, struct.pack("<12f", *[Bm[r][c] for r in range(3) for c in range(4)]))
            mu.mem_write(x2, struct.pack("<3f", *Sc))
        elif off == 0x50:
            st["set"].append((x3 & 0xFFFFFFFF, list(struct.unpack("<12I", mu.mem_read(x1, 48))), list(struct.unpack("<3I", mu.mem_read(x2, 12)))))
        elif off == 0xA0:
            ret = x1 & 0xFFFF
        mu.reg_write(UC_ARM64_REG_X0, ret)
        mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
    m.hook_add(UC_HOOK_CODE, hk, begin=H.FAKE, end=H.FAKE + 0xFFF)
    rng = random.Random(0x26DF700)
    cases = []
    for case in range(80):
        hair = u.alloc(0x400); res = u.alloc(0x200); arr = u.alloc(0x80); lst = arr + 0x30
        actor = u.alloc(0x300); model = u.alloc(0x80); pp = u.alloc(0x10); qq = u.alloc(0x10); kobj = u.alloc(0x10)
        u.wq(kobj, vt); u.wq(qq, kobj); u.wq(pp, qq)
        u.wq(hair + 0x350, res); u.wq(res + 0x158, arr); m.mem_write(arr + 0x5C, b"\x01\x01")
        u.wq(hair + 0x10, actor); u.wq(actor + 0x208, 0); u.u32(hair + 0x11C, 7); u.wq(hair + 0x3A0, model)
        u.u32(model + 0x38, 1); u.wq(model + 0x40, pp)
        pool = [u.alloc(0xA0) for _ in range(8)]
        for a, b in zip(pool, pool[1:] + [0]):
            u.wq(a, b)
        u.wq(hair + 0x318, 0); u.wq(hair + 800, pool[0]); u.u32(hair + 0x330, 0); u.u32(hair + 0x334, 8)
        flag = case % 3 == 2
        m.mem_write(hair + 0x338, bytes([1 if flag else 0]))
        n = rng.randint(1, 3)
        elems = u.alloc(8 * n)
        u.u32(lst + 8, n); u.wq(lst + 0x10, elems); u.wq(lst + 0x18, 0)
        st["bind"] = {}
        params = []
        for i, nm in enumerate(rng.sample(bone_names, n)):
            e = u.alloc(0x80)
            u.wq(elems + 8 * i, e)
            m.mem_write(e + 0x6C, b"\x01" * 5)
            u.wq(e + 0x30, u.cstr(nm))
            ang = [f32(rng.uniform(-3.2, 3.2)) for _ in range(3)] if case % 4 else [0.0, 0.0, 0.0]
            scl = [f32(rng.choice([rng.uniform(0.3, 2.0), 0.0, 0.01, -1.0, 1.0])) for _ in range(3)]
            trn = [f32(rng.uniform(-0.2, 0.2)) for _ in range(3)]
            m.mem_write(e + 0x38, struct.pack("<f", f32(rng.uniform(0, 1))))
            m.mem_write(e + 0x48, struct.pack("<3f", *ang)); m.mem_write(e + 0x54, struct.pack("<3f", *scl)); m.mem_write(e + 0x60, struct.pack("<3f", *trn))
            bi = bone_names.index(nm)
            q = [rng.uniform(-1, 1) for _ in range(4)]
            ql = math.sqrt(sum(v * v for v in q))
            w, x, y, z = (v / ql for v in q)
            R = [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                 [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                 [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]
            Bm = [[f32(R[r][0]), f32(R[r][1]), f32(R[r][2]), f32(rng.uniform(-0.3, 0.3))] for r in range(3)]
            Sc = [f32(rng.uniform(0.5, 1.5)) for _ in range(3)]
            st["bind"][bi] = (Bm, Sc)
            params.append({"bone": bi, "rotation": [fb(v) for v in ang], "scale": [fb(v) for v in scl], "transform": [fb(v) for v in trn],
                           "bind": [fb(Bm[r][c]) for r in range(3) for c in range(4)], "bindScale": [fb(v) for v in Sc]})
        root_bi = params[0]["bone"]
        if flag:
            m.mem_write(hair + 0x348, struct.pack("<HH", 0, root_bi))
        st["set"] = []
        u.call(H.F, hair)
        assert len(st["set"]) == len(params), (case, len(st["set"]), len(params))
        for p, (gidx, mat, sc) in zip(params, st["set"]):
            p["swapTransform"] = bool(flag and p["bone"] == root_bi)
            p["outBone"] = gidx
            p["outMatrix"] = mat
            p["outScale"] = sc
        cases.append(params)
    return {"function": "0x71026df700", "cases": cases, "libmCalls": len(u.libm),
            "stubs": ["hair model bone vt+0x40/+0x68/+0x50/+0xa0 python", "PLT sinf/cosf = python math rounded to f32 (not SDK libm)", "actor+0x208 = 0: AnimReduceRt weight path not run"]}


# --------------------------------------------------------------------------- clip name
def clip_section():
    u = GUC()
    m = u.mu
    LOOKUP = STUB + 0x700
    st = {"clips": set(), "log": []}

    def hook(mu, addr, size, data):
        s = u._cstr(u.rq(mu.reg_read(UC_ARM64_REG_X2))).decode()
        st["log"].append(s)
        mu.reg_write(UC_ARM64_REG_X0, 0 if s in st["clips"] else 0xFFFFFFFF)
    m.hook_add(UC_HOOK_CODE, hook, begin=LOOKUP, end=LOOKUP)
    binder = u.alloc(0x40); bvt = u.alloc(0x100); u.wq(binder, bvt); u.wq(bvt + 0x18, LOOKUP)
    keystr = {k: u.cstr(k) for k in ("WeaponVariation", "EmoteVariation", "AnimationDriven")}

    def make(cat, det, emo):
        r = u.alloc(0x300)
        u.wq(r + 8, binder); u.wq(r + 0x10, u.cstr(cat)); u.wq(r + 0x18, u.cstr(det)); u.wq(r + 0x20, u.cstr(emo))
        ring = u.alloc(0x58 * 4)
        for i in range(4):
            u.wq(ring + 0x58 * i + 8, u.alloc(0x40)); u.u32(ring + 0x58 * i + 0x10, 0x40)
        u.wq(r + 0x28, ring); u.u32(r + 0x30, 4); u.u32(r + 0x34, 0); u.u32(r + 0x38, 0)
        u.wq(r + 0x1A8, u.alloc(0x40)); u.u32(r + 0x1B0, 0x40)
        return r
    lst = u.alloc(0x20); arr = u.alloc(0x40); p = u.alloc(0x20); nbuf = u.alloc(0x100)
    names = ["WaitHold_Nrml", "Walk_Nrml", "JumpShoot_Nrml00_St", "Emote_@", "Shoot_BBll", "Shoot_Glng", "Hold_Brush", "Hold_Twins",
             "Hold_Umbrella", "Plain", "WalkBackHold_Nrml", "A_Nrml_Nrml_@_@", "X" * 70 + "_Nrml"]
    variants = [("Shtr", "Shtr", "Win01"), ("Rllr", "RllrHeavy", "Win02")]
    key_sets = [[], ["WeaponVariation"], ["EmoteVariation"], ["WeaponVariation", "EmoteVariation"], ["WeaponVariation", "EmoteVariation", "AnimationDriven"]]
    cases = []
    rng = random.Random(0x244D0B0)
    for cat, det, emo in variants:
        r = make(cat, det, emo)
        for name in names:
            pool = sorted({name.replace(a, b, 1)[:63] for a, b in [("Nrml", det), ("Nrml", cat), ("@", emo), ("@", "Win01"), ("BBll", "Slsh"), ("Glng", "Spnr"), ("Brush", "Brsh"), ("Twins", "Mnvr"), ("Umbrella", "Shlt"), ("Nrml", "Shtr")]} | {name[:63]})
            for keys in key_sets:
                for trial in range(4):
                    clips = set(rng.sample(pool, rng.randint(0, min(2, len(pool)))))
                    st["clips"] = clips
                    u.u32(lst, len(keys))
                    for i, k in enumerate(keys):
                        u.wq(arr + 8 * i, keystr[k])
                    u.wq(lst + 8, arr)
                    m.mem_write(nbuf, name.encode() + b"\0"); u.wq(p, nbuf); u.wq(p + 8, lst); m.mem_write(p + 0x10, b"\0")
                    m.mem_write(r + 0x1FC, b"\x01")
                    st["log"] = []
                    ret = u.call(0x710244D0B0, r, p)
                    cases.append({"name": name, "keys": keys, "detail": det, "category": cat, "emote": emo, "clips": sorted(clips),
                                  "tried": list(st["log"]), "returned": u._cstr(ret).decode()})
    return {"function": "0x710244d0b0", "cases": cases, "stubs": ["binder lookup vt+0x18: name recorded, 0/-1 by supplied set"]}


# --------------------------------------------------------------------------- lod
def lod_section():
    u = GUC()
    unit = u.alloc(0x40); rec = u.alloc(0x80); sphere = u.alloc(0x20)
    rng = random.Random(0x3788760)
    cases = []
    for k in range(600):
        n = [3, 3, 3, 1, 2, 5][k % 6]; mn = (k // 6) % 2; h = (10.0, 0.0, 2.0)[(k // 12) % 3]; bias = (0.0, 25.0)[(k // 36) % 2]
        start, end = (20.0, 50.0)
        inv = f32(1 / (end - start))
        z = f32(rng.uniform(-80, 5)); r = f32(rng.uniform(0, 3)); base = f32(rng.choice([0.0, 0.0, rng.uniform(-5, 5)])); old = rng.randrange(0, max(n, 1))
        rb = bytearray(0x80)
        struct.pack_into("<3f", rb, 0, start, 2 * start - end, inv)
        for j in range(3, 12):
            struct.pack_into("<f", rb, j * 4, f32(2 ** (-j + 1)))
        struct.pack_into("<f", rb, 0x5C, r)
        ub = bytearray(0x40)
        struct.pack_into("<Q", ub, 8, unit + 0x10); ub[0x10] = old; ub[0x11] = 0
        struct.pack_into("<ff", ub, 0x14, 0.5, z)
        u.mu.mem_write(unit, bytes(ub)); u.mu.mem_write(rec, bytes(rb)); u.mu.mem_write(sphere, bytes(rb[0x50:0x70]))
        u.mu.mem_write(0x7105999D58, b"\x01"); u.f32(0x7105999D5C, bias); u.f32(0x7105999D60, h)
        u.call(0x7103788760, unit, mn, n, rec, 0, sphere, fargs=(base,))
        cases.append({"zView": fb(z), "radius": fb(r), "start": fb(start), "inverseGap": fb(inv), "viewInput": fb(base), "bias": fb(bias),
                      "hysteresis": fb(h), "count": n, "minimum": mn, "old": old, "stage": u.mu.mem_read(unit + 0x10, 1)[0]})
    return {"function": "0x7103788760", "mode": "distance, internal storage, not fixed", "cases": cases}


# --------------------------------------------------------------------------- curves
def curve_section():
    import material_animation_r9_emu as MA
    u = GUC()
    # web data file (curves with BfresLibrary flag word: CurveType|FrameType|KeyType|Pre<<8|Post<<12)
    dump = json.loads((ROOT / "web/games/splatoon3/assets/characters/Player00/data/tank_anim_native.json").read_text(encoding="utf-8"))
    curves = []
    for ba in dump["skeletal"]["Gauge"]["bones"]:
        for c in ba["curves"]:
            curves.append(("skeletal:Gauge:" + ba["name"], c))
    for a in dump["material"]["clips"]:
        for mat in a["materials"]:
            for ci, c in enumerate(mat["curves"]):
                curves.append((f"material:{a['name']}:{mat['material']}:{ci}", c))
    out = []
    for label, c in curves:
        if c["type"] not in ("Cubic", "Linear"):
            continue
        p = MA.descriptor(u, c)
        cache = u.alloc(16)
        for fr in sorted(set([-1.0, 0.0, 0.5, 1.0, 37.0, 44.0, 45.0, 99.0, 100.0, 101.0] + [float(v) for v in c["frames"]] + [f32(i * 0.37) for i in range(0, 280, 7)])):
            u.mu.mem_write(cache, struct.pack("<fIII", float("inf"), 0, 0, 0))
            u.call(0x710088E380, p, cache, fargs=(fr,))
            out.append({"curve": label, "frame": fb(f32(fr)), "result": u.mu.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF})
    return {"function": "0x710088e380", "source": "assets/characters/Player00/data/tank_anim_native.json (raw Tnk_Simple.bfres, graphics_bfres2gltf dump --keys)", "samples": out,
            "note": "FSKA Scale curve evaluated with the FRES float curve reader; whether the skeletal binder calls this exact reader is [미확정]"}


# --------------------------------------------------------------------------- cloth
def cloth_section():
    import numpy as np
    from unicorn import UC_HOOK_MEM_INVALID
    from unicorn.arm64_const import UC_ARM64_REG_TPIDR_EL0
    e = GUC()
    rng = random.Random(0x11C107)
    a = e.alloc(16); b = e.alloc(16)
    pow_cases = []
    for i in range(512):
        base = f32([.999, 1.0, .5, .999999, 1.5][i % 5] if i < 20 else rng.uniform(.001, 1.8))
        ex = f32([0, 1 / 60, 1 / 30, 4 / 60, -1 / 60][i % 5] if i < 20 else rng.uniform(-.2, .4))
        e.mu.mem_write(a, struct.pack("<4f", *[base] * 4)); e.mu.mem_write(b, struct.pack("<4f", *[ex] * 4))
        e.call(0x71008A63E0, a, b)
        pow_cases.append([fb(base), fb(ex), e.mu.reg_read(UC_ARM64_REG_S0) & 0xFFFFFFFF])
    # DC42A0 coefficient + EE41F0 integration (r9 harness objects)
    tls = e.alloc(0x100); hc = e.alloc(0x400); router = e.alloc(0x100); arena = e.alloc(0x60); scratch = e.alloc(0x400)
    e.mu.reg_write(UC_ARM64_REG_TPIDR_EL0, tls); e.wq(tls + 0x68, hc); e.wq(hc + 0x3D0, router); e.wq(router + 0x10, arena); e.wq(arena + 8, 1)
    e.wq(0x71057D7088, STUB + 0x820); e.wq(0x71057D7090, STUB + 0x828)

    def alloc_hook(mu, ad, size, user):
        if ad == STUB + 0x820:
            mu.reg_write(UC_ARM64_REG_X0, scratch)
    e.mu.hook_add(UC_HOOK_CODE, alloc_hook, begin=STUB + 0x820, end=STUB + 0x828)
    sim = e.alloc(0x300); data = e.alloc(0x300); parts = e.alloc(16 * 9); cur = e.alloc(16 * 9); prev = e.alloc(16 * 9)
    op = e.alloc(0x70); cfg = e.alloc(0x30); ctx = e.alloc(0x20); world = e.alloc(0x128); ci = e.alloc(0x200); cd = e.alloc(0x100); arr = e.alloc(8)
    e.wq(sim + 0x18, data); e.wq(data + 0x40, parts); e.wq(sim + 0x20, cur); e.wq(sim + 0x30, prev)
    e.wq(op + 0x50, cfg); e.u32(op + 0x20, 0x7FFFFFFF); e.wq(ctx + 8, world); e.wq(ctx + 16, ci); e.wq(ci + 0x40, arr); e.wq(arr, sim); e.wq(ci + 0x18, cd)
    integ = []
    for i in range(160):
        dt = f32([1 / 60, 1 / 30, 4 / 60, -1 / 60][i % 4] if i < 16 else rng.uniform(.002, .2))
        damp = f32([0, .001, .5, 1, 1.2, -.2][i % 6] if i < 24 else rng.uniform(-.1, 1.2))
        sub = 1 + i % 4; scale = f32([.5, 1, 2][i % 3]); kind = 1 if i % 5 == 0 else 2; n = 1 + i % 9
        grav = [0.0, f32(-9.81), 0.0, 0.0] if i % 2 == 0 else [f32(rng.uniform(-10, 10)) for _ in range(4)]
        e.mu.mem_write(data + 0x20, struct.pack("<4f", *grav)); e.f32(data + 0x30, damp); e.u32(sim + 0x140, kind); e.f32(sim + 0x144, scale)
        e.f32(sim + 0x50, 0); e.f32(sim + 0x54, .31); e.mu.mem_write(cfg + 0x28, bytes([sub])); e.f32(ctx, dt)
        e.call(0x7100DC42A0, op, ctx)
        eff = e.ru32(sim + 0x50); co = e.ru32(sim + 0x54)
        pos = [[f32(rng.uniform(-5, 5)) for _ in range(4)] for _ in range(n)]
        old = [[f32(rng.uniform(-5, 5)) for _ in range(4)] for _ in range(n)]
        props = [[f32(.7142857313156128), f32(1.399999976158142), f32(.05), f32(.5)] if j < n - 2 else [0.0, 0.0, f32(.05), f32(.5)] for j in range(n)]
        e.mu.mem_write(cur, b"".join(struct.pack("<4f", *v) for v in pos)); e.mu.mem_write(prev, b"".join(struct.pack("<4f", *v) for v in old))
        e.mu.mem_write(parts, b"".join(struct.pack("<4f", *v) for v in props)); e.u32(sim + 0x28, n)
        e.call(0x7100EE41F0, 0, sim, fargs=(bf(eff),))
        got = list(struct.unpack("<%dI" % (4 * n), e.mu.mem_read(cur, 16 * n)))
        integ.append({"dt": fb(dt), "damping": fb(damp), "substeps": sub, "scale": fb(scale), "kind": kind, "gravity": [fb(v) for v in grav],
                      "effectiveDt": eff, "coefficient": co, "current": [fb(v) for r in pos for v in r], "previous": [fb(v) for r in old for v in r],
                      "props": [fb(v) for r in props for v in r], "out": got})
    # D47BD0 Standard / D1C354 Bend (r9 harness objects)
    c = e.alloc(0x40); ln = e.alloc(20); sim2 = e.alloc(0x50); data2 = e.alloc(0x60); parts2 = e.alloc(0x20); pos2 = e.alloc(0x20)
    e.wq(c + 0x28, ln); e.u32(c + 0x30, 1); e.wq(sim2 + 0x18, data2); e.wq(data2 + 0x40, parts2); e.wq(sim2 + 0x20, pos2)
    links = []
    for i in range(400):
        bend = i % 2 == 1
        wa = f32(rng.choice([rng.uniform(0, 3), 1.399999976158142, 0.0])); wb = f32(rng.choice([rng.uniform(0, 3), 1.399999976158142]))
        scalar = f32([0, -.5, .25, 1, 2][i % 5])
        pa = [f32(rng.uniform(-2, 2)) for _ in range(4)]
        if bend:
            lo = f32(.25); hi = f32(1.0); kb = f32(rng.uniform(0, 1)); ks = f32(rng.uniform(0, 1))
            d = [f32(rng.uniform(-1, 1)) for _ in range(4)]
            mul = f32([0, .1, .5, 2, 4][(i // 2) % 5]); d = [f32(v * mul) for v in d[:3]] + [d[3]]
            pb = [f32(pa[k] + d[k]) for k in range(4)]
            e.mu.mem_write(ln, struct.pack("<HHffff", 0, 1, lo, hi, kb, ks))
            params = {"bendMinLength": fb(lo), "stretchMaxLength": fb(hi), "bendStiffness": fb(kb), "stretchStiffness": fb(ks)}
            fn = 0x7100D1C354
        else:
            rest = f32(rng.uniform(0, .9)); st = f32(rng.choice([rng.uniform(0, 1), 0.7142857313156128, 0.3571428656578064]))
            pb = [f32(rng.uniform(-2, 2)) for _ in range(4)]
            e.mu.mem_write(ln, struct.pack("<HHff", 0, 1, rest, st))
            params = {"restLength": fb(rest), "stiffness": fb(st)}
            fn = 0x7100D47BD0
        e.f32(parts2 + 4, wa); e.f32(parts2 + 0x14, wb); e.mu.mem_write(pos2, struct.pack("<8f", *(pa + pb)))
        e.wq(c + 0x28, ln)
        e.call(fn, c, sim2, fargs=(scalar,))
        links.append({"bend": bend, **params, "invMass": [fb(wa), fb(wb)], "scalar": fb(scalar), "a": [fb(v) for v in pa], "b": [fb(v) for v in pb],
                      "out": list(struct.unpack("<8I", e.mu.mem_read(pos2, 32)))})
    return {"functions": ["0x71008a63e0", "0x7100dc42a0", "0x7100ee41f0", "0x7100d47bd0", "0x7100d1c354"], "pow": pow_cases, "integrate": integ, "links": links,
            "fixtures": ["r9 synthetic hcl objects (scratch alloc, force count 0, profiler null)"], "pltStubbed": sorted(set(e.plt_stubbed))}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = {"sourceSHA256": hashlib.sha256((ROOT / "extracted/exefs/main.reloc.img").read_bytes()).hexdigest()}
    for name, fn in [("tank", tank_section), ("head", head_section), ("teamRandom", team_section), ("hairArrange", hair_section),
                     ("clipName", clip_section), ("lod", lod_section), ("curves", curve_section), ("cloth", cloth_section)]:
        res[name] = fn()
        n = len(res[name].get("cases", res[name].get("sequences", res[name].get("samples", res[name].get("links", [])))))
        print(name, n, json.dumps({k: v for k, v in res[name].items() if k in ("constants", "staticInit", "pltStubbed", "libmCalls")}))
    OUT.write_text(json.dumps(res, separators=(",", ":")) + "\n", encoding="utf-8")
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
