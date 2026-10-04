"""r10 analysis-only: execute original bphsh attachment including native TAG0 loader.

Original library initialization is reused; no loader/type-introspection stubs are
installed. Failure, null calls, page synthesis and external boundaries are saved.
This is a loader probe, not a whole camera/stage broadphase claim.
"""
import json
import sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_PC
from r8_physics_native_uc import init_native
from collision_mesh import load_blobs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/camera_100_r10/boom"
sys.stdout.reconfigure(encoding="utf-8")
u, errors = init_native()
u.wq(0x710599dfa8, 0)
u.wq(0x71059975c0, 0)
trace = []
for p in (0x7100bb3edc, 0x7100ba11cc, 0x71008b45c0, 0x71008b4834):
    u.mu.hook_add(UC_HOOK_CODE, lambda mu, pc, size, ud: trace.append(hex(pc)), begin=p, end=p)
raws = load_blobs(ROOT / "extracted/romfs/Pack/Actor/Fld_VSLobby.pack.zs")
name, raw = raws[0]
p = u.alloc(len(raw))
u.mu.mem_write(p, raw)
owner = u.alloc(0x100)
u.trace_blocks(loop_limit=10000)
err = u.call(0x7103a715b4, owner, p, len(raw), 0, count=5000000)
out = dict(scope=__doc__, file=name, length=len(raw), errors=errors,
           loader_error=err, end_pc=hex(u.mu.reg_read(UC_ARM64_REG_PC)),
           owner=hex(owner), owner_bytes=bytes(u.mu.mem_read(owner, 0x80)).hex(),
           native_shape=hex(u.rq(owner + 0x70)), trace=trace,
           null_calls={str(k): v for k, v in u.null_calls.items()},
           null_writes={hex(k): v for k, v in u.null_writes.items()},
           faults=u.faults, auto_pages=u.auto_pages, plt=u.plt_stubbed,
           os=u.os_calls, blocks=[hex(x) for x in u.blocks])
if u.rq(owner + 0x70):
    h = u.rq(owner + 0x70)
    out['native_header'] = bytes(u.mu.mem_read(h, 0x100)).hex()
    out['native_vt'] = hex(u.rq(h))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "tag0_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: out[k] for k in ('file','loader_error','end_pc','native_shape','native_vt','faults','auto_pages','null_calls','plt') if k in out}, ensure_ascii=False))
