"""Actual camera-request write blocks and ActorRef binder; synthetic inputs.

Contact selection, named transform lookup, whole actors and scene are not run.
No function, SDK, PLT or mathematical stub is used by the executed ranges.
"""
import json
import random
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC, BASE, STACK, STUB

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'


def main():
    uc = UC()
    mu = uc.mu
    rng = random.Random(101036)
    b = uc.alloc(0xb000)
    behavior = uc.alloc(0x120)
    owner = uc.alloc(0x400)
    component = uc.alloc(0x300)
    handle = uc.alloc(0x100)
    mu.mem_write(behavior + 0x108, struct.pack('<Q', b))
    mu.mem_write(component + 0x10, struct.pack('<Q', owner))
    mu.mem_write(owner + 0x10, struct.pack('<I', 17))
    rows = []
    native_calls = {hex(BASE + 0x3c838dc): 0}
    stub_calls = []

    def audit(m, address, size, _):
        if address == BASE + 0x3c838dc:
            native_calls[hex(address)] += 1
        if STUB <= address < STUB + 0x1000:
            stub_calls.append(hex(address))
            raise AssertionError(('unexpected stub', hex(address)))

    mu.hook_add(UC_HOOK_CODE, audit)
    for kind, start, end in [('GateManhole', 0x2153a5c, 0x2153ac8),
                             ('MissionGateway', 0x21b9f60, 0x21b9fcc)]:
        for i in range(384):
            enabled = [0, 1, 255][i % 3]
            actor_state = [0, 6, 7, 8, 9, 10, 11, 12][(i // 3) % 8]
            valid_handle = (i // 24) % 2 == 0
            old_ref = bytearray(rng.randbytes(24))
            struct.pack_into('<I', old_ref, 0x10, 0xffffffff)
            old_ref[0x14] = enabled  # B932c is inside this ActorRef, not a separate byte.
            new_ref = bytearray(old_ref)
            payload = rng.randbytes(48)  # Includes arbitrary float/NaN payloads; byte copy.
            local_stack = STACK + 0xe0000
            mu.mem_write(local_stack, payload)
            mu.mem_write(b + 0x9318, bytes(old_ref))
            mu.mem_write(b + 0x932c, bytes([enabled]))
            mu.mem_write(b + 0x9314, b'\x7e\x00')  # Preserve active; set request.
            mu.mem_write(b + 0x9330, b'\xa5' * 48)
            mu.mem_write(owner + 0x1a8, struct.pack('<Q', handle if valid_handle else 0))
            mu.mem_write(owner + 0x24, struct.pack('<I', actor_state))
            mu.mem_write(component + 0x1ef, b'\x7e')
            if enabled and valid_handle and actor_state not in range(7, 12):
                struct.pack_into('<Q', new_ref, 8, handle)
                struct.pack_into('<I', new_ref, 0x10, 17)
                new_ref[0x15] = 0
            mu.reg_write(UC_ARM64_REG_X19, component)
            mu.reg_write(UC_ARM64_REG_X20, behavior)
            mu.reg_write(UC_ARM64_REG_SP, local_stack)
            mu.reg_write(UC_ARM64_REG_X29, STACK + 0xef000)
            mu.reg_write(UC_ARM64_REG_X1, owner)
            mu.emu_start(BASE + start, BASE + end, count=500)
            actual_ref = bytes(mu.mem_read(b + 0x9318, 24))
            assert actual_ref == bytes(new_ref), (kind, i, actual_ref.hex(), new_ref.hex())
            assert bytes(mu.mem_read(b + 0x9330, 48)) == payload, (kind, i, 'local copy')
            assert bytes(mu.mem_read(b + 0x9314, 2)) == b'\x7e\x01'
            if kind == 'MissionGateway':
                assert bytes(mu.mem_read(component + 0x1ef, 1)) == b'\x01'
            rows.append(dict(owner=kind, enabled=enabled, actor_state=actor_state,
                             valid_handle=valid_handle, old_ref=old_ref.hex(),
                             input_local=payload.hex(), output_ref=actual_ref.hex(),
                             active=126, request=1))
    result = dict(scope='synthetic selected request write blocks, original ActorRef initial binding; '
                        'no contact/named-matrix lookup, old valid-ref replacement or scene run',
                  counts={'GateManhole': 384, 'MissionGateway': 384}, mismatch=0,
                  native_calls=native_calls, stub_calls=stub_calls,
                  function_stubs=0, sdk_stubs=0, plt_stubs=0,
                  arbitrary_math_stubs=0, cases=rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'request_results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('counts', 'mismatch', 'native_calls', 'stub_calls')}))


if __name__ == '__main__':
    main()
