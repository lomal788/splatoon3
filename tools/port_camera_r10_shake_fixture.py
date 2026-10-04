"""Port regression: existing r10 original shake instructions -> persistent JSON fixture.
No decompilation or new analysis completion claims. The original projection is captured,
SDK allocation/mutex/guards are supplied. Pose/owner/parameter graphs are synthetic.
"""
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "web/tools/r10_camera_shake_emu.py"
ns = {"__file__": str(SOURCE)}
# Reuse the proven harness/parameter factories without rerunning/writing the old audit.
exec(SOURCE.read_text(encoding="utf-8").split("counts=Counter();examples=[]")[0], ns)
e, parameter, instance, result = (ns[n] for n in ("e", "parameter", "instance", "result"))
data = ns["data"]
bits3 = lambda address: list(struct.unpack("<3I", e.mu.mem_read(address, 12)))

traces = []
ticks = 0
for name, param in data.items():
    if param["Curve"]["Type"] not in ("Linear", "Hermit"):
        continue
    p, h = parameter(param)
    for gain in (0.375, 0.7, 1):
        for scenario in ("unfollowed_absent", "matching", "stale", "removed_at3", "generation_at4", "limit3"):
            owner = e.alloc(0x28)
            e.w32(owner + 0x20, 10 if scenario == "stale" else 9)
            follow = scenario != "unfollowed_absent"
            limit = 3 if scenario == "limit3" else -1
            slot = instance(p, h, gain=gain, limit=limit, follow=int(follow),
                            owner=owner if follow else 0)
            module = e.alloc(0x350)
            e.w32(module + 0x130, 1)
            e.w64(module + 0x138, slot)
            e.mu.mem_write(module + 0xd4, struct.pack("<3f4f", 0, 0, 0, 0, 0, 0, 1))
            trace = []
            for tick in range(int(param["Curve"]["MaxX"]) * 2 + 3):
                if scenario == "removed_at3" and tick == 3:
                    e.w64(slot + 0x38, 0)
                if scenario == "generation_at4" and tick == 4:
                    e.w32(owner + 0x20, 10)
                e.call(0x7101010150, [module])
                frame, elapsed = struct.unpack("<2i", e.mu.mem_read(slot + 0x14, 8))
                trace.append({"tick": tick, "frame": frame, "elapsed": elapsed,
                              "valid": bool(e.r64(slot)),
                              "finished": bool(result(0x7101018b4c, slot)),
                              "output_bits": bits3(slot + 0x1c),
                              "offset_bits": bits3(module + 0x144)})
                ticks += 1
            traces.append({"name": name, "param": param, "gain": gain,
                           "scenario": scenario, "limit": limit, "trace": trace})

previous = json.loads((ROOT / "analysis/camera_100_r10/shake/native_emu.json").read_text(encoding="utf-8"))
audit = json.loads((ROOT / "analysis/camera_100_r10/shake/data_audit.json").read_text(encoding="utf-8"))
admissions = []
for admission in previous["elink_admissions"]:
    asset = next(a for a in audit["assets"][admission["user"]] if a["key"] == admission["key"])
    params = dict(asset["params"])
    for key in ("CameraRumbleName", "CameraRumbleFrame", "CtrlRumbleName", "DistanceAttenuate"):
        if key in asset:
            params[key] = asset[key]
    admissions.append({**admission, "params": params})
fixture = {
    "version": "Splatoon3 v0 r10 camera shake port",
    "scope": "Original whole Module1010150->instance10182e8->finished1018b4c, projection captured; SDK heap/mutex/guard boundary, synthetic owner/parameter/pose. Existing admission40 reused, not rerun or counted as new analysis.",
    "original_functions": ["0x7101010150", "0x71010182e8", "0x7101018b4c"],
    "trace_cases": len(traces), "native_ticks": ticks, "traces": traces,
    "elink_admissions_reused": admissions,
    "boundaries": {"SDK": dict(e.sdklog), "allocation": {hex(k): v for k, v in e.stublog.items()},
                   "captured": dict(e.captured)},
    "not_verified": ["full scene/ELink owner generation producer/delay", "controller hardware",
                     "actual Module capacity", "runtime inherited resource generation producer",
                     "Sin/other weapon curves"],
}
out = ROOT / "analysis/port_camera_r10/shake"
out.mkdir(parents=True, exist_ok=True)
dest = ROOT / "web/games/splatoon3/tests/fixtures/camera_shake_r10_native.json"
dest.write_text(json.dumps(fixture, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
(out / "native_fixture_result.json").write_text(json.dumps({"trace_cases": len(traces), "native_ticks": ticks,
    "fixture": dest.relative_to(ROOT).as_posix(), "scope": fixture["scope"],
    "boundaries": fixture["boundaries"], "not_verified": fixture["not_verified"]},
    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"trace_cases": len(traces), "native_ticks": ticks, "fixture": str(dest)}, ensure_ascii=False))
