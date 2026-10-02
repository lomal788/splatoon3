"""r6 combat: 히트 이펙트 행(HitEffectorType) 선택 0x71028fed18 원본 실행(unicorn).

호출: 0x71016d9c60 이 0x71028fed18(info+4 = 생성정보+8 카테고리, info+8 = 생성정보+0xc 무기 ID, info+0xc = 탄 슬롯95 ExtraInfo).
표: 무기 정보 행 빌더 0x7101413a60 이 노드+0x28[0..25] 를 행+0x50(DefaultHitEffectorType) 으로 채우고(0x7101413b6c~0x7101413ba4),
    ExtraHitEffectorInfoSet 항목마다 [ExtraInfo] 칸을 덮어씀(0x7101414154).
이 도구: WeaponInfoMain 데이터로 같은 트리를 메모리에 만들고 0x71028fed18 을 그대로 실행해 재구현과 비교.
카테고리 1/2 표(+0xd8)와 무기 ID 특수 구간(음수·4xxxx·5xxxx)은 합성 트리/값으로 실행.
스텁: 없음(함수는 메모리 읽기만). 트리 모양은 정렬 사슬(불균형) — 원본 트리 균형은 결과에 영향 없음.
사용: PY web/tools/r6_combat_hiteffect_emu.py
"""
import json
import random
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_uc import UC, BASE  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HET = [s.strip() for s in "Default , Shooter , Shooter_CriticalHit , Roller , Roller_NoDamage , Charger , Charger_FullCharge , Charger_PaintSplash , Slosher , Slosher_Big , Slosher_Bathtub , Slosher_WashtubBombCore , Slosher_LauncherLeader , Slosher_LauncherFollower , Slosher_BearLeader , Spinner , Blaster , Blaster_ExtraBombCore , Blaster_ExtraBombCoreWeak , Maneuver , Shelter , Saber , Saber_Shot , Saber_ChargeShot , Saber_Slash , Saber_ChargeSlash , Bomb , Bomb_Fizzy , Bomb_Torpedo , Bomb_Curling , LineMarker , Sprinkler , Sprinkler_Ink , PaintSplash , PaintSplashExplosion , UltraShot , InkStorm , NiceBall , Blower_Inhale , ShockSonar_Wave , MultiMissile_Bullet , MultiMissile_BombCore , Jetpack_Launcher , UltraStamp , Skewer_BombCore , SuperLanding , SalmonBuddy , GoldenIkuraAttack".split(",")]
EXI = [s.strip() for s in "Normal , FullCharge , RollerCore , ExtraBombCore , BlasterWeakBlast , ExtraPaintSplash , ExtraPaintSplashExplosion , SlosherLauncherFollower , ShooterVariableRepeat , ShelterCanopy , UltraStampSwing , BlowerInhale , ShockSonarWave , SaberShot , SaberChargeShot , SaberSlash , SaberChargeSlash , CriticalHit , CurlingDirectHit , MultiMissileDirectHit , JetpackJet , RollerInkNoDamage , SlosherBig , SprinklerInk , ChariotBody , GoldenIkuraAttack".split(",")]


def ref(cat, wid, ex, tables):
    s32 = lambda v: v - (1 << 32) if v & 0x80000000 else v
    wid, ex = s32(wid & 0xFFFFFFFF), s32(ex & 0xFFFFFFFF)
    if wid < 0:
        return 0x1A if ex == 3 else 0
    band = (wid // 10000) * 10000
    if band == 50000:
        r = 0x28 if ex == 0x13 else 0x29
        return 0x1A if (wid == 50010 and cat == 1) else r
    if band == 40000:
        if cat == 1:
            return 0x1A if wid == 40000 else (0x21 if ex == 5 else 0)
        if cat == 0 and wid == 42000:
            return 7 if ex == 5 else (6 if ex == 1 else 5)
        return 0x21 if ex == 5 else 0
    if cat in (0, 1, 2):
        node = tables[cat].get(wid)
        if node is None:
            return 0
        return node[ex] if (ex & 0xFFFFFFFF) < 0x1A else node[0]
    return 0x2F if ex == 0x19 else 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    h = UC()
    mu = h.mu
    mu.mem_map(0x40000000, 0x1000000)
    h.heap_next = 0x40000000
    rows = json.load(open(ROOT / "analysis/combat/rsdb/WeaponInfoMain.json", encoding="utf-8"))
    tab0 = {}
    for r in rows:
        arr = [HET.index(r["DefaultHitEffectorType"])] * 26
        for e in r.get("ExtraHitEffectorInfoSet", []):
            arr[EXI.index(e["ExtraInfo"])] = HET.index(e["HitEffectorType"])
        tab0[int(r["Id"])] = arr
    rng = random.Random(20261003)
    tab1 = {i: [rng.randrange(48) for _ in range(26)] for i in rng.sample(range(0, 40000), 30)}
    tab2 = {i: [rng.randrange(48) for _ in range(26)] for i in rng.sample(range(0, 40000), 30)}
    tables = {0: tab0, 1: tab1, 2: tab2}

    def build(tab):
        keys = sorted(tab)
        nodes = {}
        for k in keys:
            n = h.alloc(0x98)
            h.u32(n + 0x20, k)
            mu.mem_write(n + 0x28, struct.pack("<26I", *tab[k]))
            nodes[k] = n
        for a, b in zip(keys, keys[1:]):
            mu.mem_write(nodes[a] + 0x10, struct.pack("<Q", nodes[b]))
        holder = h.alloc(8)
        mu.mem_write(holder, struct.pack("<Q", nodes[keys[0]]))
        return holder
    obj = h.alloc(0x40)
    base = h.alloc(0x28 * 13)
    h.u32(obj + 0x10, 13)
    mu.mem_write(obj + 0x18, struct.pack("<Q", base))
    for idx, cat, off in ((10, 0, 0x118), (11, 1, 0xD8), (12, 2, 0xD8)):
        P = h.alloc(0x200)
        mu.mem_write(P + off, struct.pack("<Q", build(tables[cat])))
        mu.mem_write(base + idx * 0x28 + 0x20, struct.pack("<Q", P))
    mu.mem_write(0x710599B420, struct.pack("<Q", obj))
    cases, bad, crit = 0, [], []
    wids = list(tab0) + list(tab1) + list(tab2) + [-1, -5, 40000, 42000, 42001, 49999, 50000, 50010, 50004, 59999, 60000, 12345]
    for cat in (0, 1, 2, 3, -1):
        for wid in wids:
            for ex in list(range(0, 28)) + [-1, 0x7FFFFFFF]:
                got = h.call(0x71028FED18, cat & 0xFFFFFFFF, wid & 0xFFFFFFFF, ex & 0xFFFFFFFF) & 0xFFFFFFFF
                exp = ref(cat, wid, ex, tables)
                cases += 1
                if got != exp:
                    bad.append({"cat": cat, "wid": wid, "ex": ex, "got": got, "exp": exp})
    for r in rows:
        if r["__RowId"].startswith("Shooter_") and r["__RowId"].endswith("_00"):
            g = h.call(0x71028FED18, 0, int(r["Id"]), 17) & 0xFFFFFFFF
            n = h.call(0x71028FED18, 0, int(r["Id"]), 0) & 0xFFFFFFFF
            crit.append({"weapon": r["__RowId"], "id": r["Id"], "normal": HET[n], "critical": HET[g]})
    out = {"function": "0x71028fed18", "cases": cases, "mismatches": bad[:50], "mismatch_count": len(bad),
           "shooter_rows_normal_vs_critical": crit,
           "stubs": [], "synthetic": ["카테고리 1/2 표는 무작위 합성", "트리는 정렬 사슬"],
           "unverified": ["실제 표 객체 *0x710599b420 를 만드는 로더와 카테고리 1/2 표 데이터(WeaponInfoSub/Special)"]}
    p = ROOT / "analysis/combat/r6_hiteffect_emu.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"0x71028fed18: {cases}건 불일치 {len(bad)}")
    for c in crit:
        print("  ", c)
    print("결과:", p)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
