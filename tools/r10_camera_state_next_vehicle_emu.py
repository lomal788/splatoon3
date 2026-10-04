"""Native VehicleSpectacle typed receiver -> command queue -> FSM callback.

Original SDK memset is linked through the original main PLT GOT cell in RAM.
Synthetic ready guards/pool/ActorRefs; stop before existing Controlled enter/exit
callbacks. These callbacks, valid handle/thread retention and scene run remain
outside execution. No function, SDK, PLT-return or mathematical stub.
"""
import json
import random
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_PC, UC_ARM64_REG_X0, UC_ARM64_REG_X1
from network_uc import UC, BASE, STUB, END

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'
SDK = 0x7400000000


def main():
    e = UC()
    mu = e.mu
    sdk = (ROOT / 'extracted/exefs/sdk.img').read_bytes()
    mod = struct.unpack_from('<I', sdk, 4)[0]
    p = mod + struct.unpack_from('<i', sdk, mod + 4)[0]
    tags = {}
    while True:
        tag, value = struct.unpack_from('<qQ', sdk, p)
        p += 16
        if not tag:
            break
        tags.setdefault(tag, value)
    symbols = []
    for i in range((tags[5] - tags[6]) // 24):
        name_off, info, other, section, value, size = struct.unpack_from('<IBBHQQ', sdk, tags[6] + i * 24)
        q = tags[5] + name_off
        name = sdk[q:sdk.index(0, q)].decode(errors='replace')
        if name == 'memset' and section:
            symbols.append(dict(name=name, offset=value, bytes=size, section=section))
    assert symbols == [dict(name='memset', offset=0x581ba8, bytes=0xd0, section=2)]
    mu.mem_map(SDK, (len(sdk) + 0xffff) & ~0xffff)
    mu.mem_write(SDK, sdk)
    # Actual original PLT3e99f10 executes ADRP/LDR/BR through cell576efa8.
    mu.mem_write(BASE + 0x576efa8, struct.pack('<Q', SDK + symbols[0]['offset']))
    component = e.alloc(0x180)
    payload = e.alloc(0x400)
    msg = e.alloc(0x20)
    behavior = e.alloc(0x120)
    body = e.alloc(0xb000)
    pool = e.alloc(0x218)
    state_records = e.alloc(0x80)
    rng = random.Random(101022)
    guards = [0x5872a60, 0x5800d90, 0x58b4220, 0x5824530]
    for guard in guards:
        mu.mem_write(BASE + guard, b'\x01')
    # Actual generic initialized FSM default descriptor, no synthesized opcode.
    mu.mem_write(BASE + 0x58244f0, struct.pack('<Q', BASE + 0x5571fa0) + b'\0' * 56)
    counts, rows, native_calls = {}, [], {}
    hit = []
    endpoints = {BASE + 0x26b0bd4: 'Controlled_enter', BASE + 0x26b0ebc: 'Controlled_exit'}
    watched = {BASE + a for a in [0x24341ac, 0x3c837c8, 0x3c83bc4, 0x1256c54,
                                 0x1256b40, 0x26b18d8, 0x26b1964, 0x125a178, 0x2b50078]}

    def audit(m, address, size, _):
        if STUB <= address < STUB + 0x1000 and address != END:
            raise AssertionError(('stub', hex(address)))
        if BASE + 0x3e90000 <= address < BASE + 0x3e9e000 and not BASE + 0x3e99f10 <= address < BASE + 0x3e99f20:
            raise AssertionError(('unlinked PLT', hex(address)))
        if address in watched or address == SDK + 0x581ba8:
            key = hex(address)
            native_calls[key] = native_calls.get(key, 0) + 1
        if address in endpoints:
            hit.append(dict(endpoint=endpoints[address], pc=hex(address),
                            object=hex(m.reg_read(UC_ARM64_REG_X0)),
                            target=m.reg_read(UC_ARM64_REG_X1)))
            m.emu_stop()

    mu.hook_add(UC_HOOK_CODE, audit)

    def u32(ptr, value):
        mu.mem_write(ptr, struct.pack('<I', value & 0xffffffff))

    def u64(ptr, value):
        mu.mem_write(ptr, struct.pack('<Q', value))

    def r32(ptr):
        return struct.unpack('<I', mu.mem_read(ptr, 4))[0]

    def r64(ptr):
        return struct.unpack('<Q', mu.mem_read(ptr, 8))[0]

    def setup(old_state, raw_position, ref_enable=1):
        mu.mem_write(component, b'\0' * 0x180)
        mu.mem_write(pool, b'\xa5' * 0x218)
        mu.mem_write(payload, b'\0' * 0x400)
        u64(component, BASE + 0x563f428)
        u64(component + 0xe0, behavior)
        u64(behavior + 0x108, body)
        mu.mem_write(body + 0x10, raw_position)
        u64(component + 0x78, BASE + 0x553c2e8)
        u32(component + 0x88, -1)
        mu.mem_write(component + 0x8c, bytes([ref_enable, 0, 0]))
        q = component + 0xa8
        u64(q, q)
        u64(q + 8, q)
        u64(q + 0x18, pool)
        u32(q + 0x28, 1)
        u64(pool, 0)
        u64(state_records, BASE + 0x5571fa0)
        mu.mem_write(state_records + 8, b'\0' * 56)
        u64(state_records + 0x40, BASE + 0x563f590)
        u64(state_records + 0x48, component)
        u64(state_records + 0x50, BASE + 0x26b0bd4)
        u64(state_records + 0x60, BASE + 0x26b0d58)
        u64(state_records + 0x70, BASE + 0x26b0ebc)
        u32(component + 0x38, old_state)
        u32(component + 0x3c, 173)
        u32(component + 0x48, 0)
        u32(component + 0x58, 2)
        u64(component + 0x60, state_records)
        u64(payload, BASE + 0x56730e0)
        u64(payload + 0xb0, BASE + 0x553c2e8)
        u32(payload + 0xc0, -1)
        mu.mem_write(payload + 0xc4, b'\x01\0\0')
        hit.clear()

    for i in range(192):
        kind = i % 3
        command = [0x6fe76000, 0x6fe76001, 0xdeadbeef][kind]
        mode = (i // 3) % 4
        position = rng.randbytes(12)
        setup(0, position, (i // 12) & 1)
        if mode == 0:
            argument = 0
        elif mode == 1:
            u64(payload, BASE + 0x56228a0)
            argument = payload
        else:
            argument = payload
        u32(msg + 4, command)
        u64(msg + 0x10, argument)
        before = bytes(mu.mem_read(component, 0x180))
        result = e.call(BASE + 0x24341ac, component, msg)
        accepted = kind == 1 or (kind == 0 and mode >= 2)
        assert result == int(accepted), (i, kind, mode, result)
        if not accepted:
            assert bytes(mu.mem_read(component, 0x180)) == before
        else:
            vt = BASE + (0x563f5c8 if kind == 0 else 0x563f600)
            assert r64(pool) == vt and r64(pool + 8) == component
            assert r32(component + 0xb8) == 1
            assert r32(pool + 0x200) == 0
            assert r64(component + 0xa8) == pool + 0x208
            assert r64(component + 0xb0) == pool + 0x208
            assert r64(pool + 0x208) == component + 0xa8
            assert r64(pool + 0x210) == component + 0xa8
            if kind == 0:
                assert bytes(mu.mem_read(component + 0x90, 12)) == position
                # Invalid handle input explicitly: no validactor retention claim.
                assert r64(component + 0x80) == 0 and r32(component + 0x88) == 0xffffffff
        counts['whole_receiver_invalid_or_empty_ref'] = counts.get('whole_receiver_invalid_or_empty_ref', 0) + 1
        rows.append(dict(group='whole_receiver_invalid_or_empty_ref', case=i, command=hex(command),
                         payload_mode=mode, result=result, accepted=accepted))

    for i in range(96):
        target = i & 1
        position = rng.randbytes(12)
        setup(1 - target, position)
        u32(msg + 4, 0x6fe76000 if target else 0x6fe76001)
        u64(msg + 0x10, payload)
        assert e.call(BASE + 0x24341ac, component, msg) == 1
        e.call(BASE + 0x1256b40, component + 0xa8)
        assert len(hit) == 1 and hit[0]['object'] == hex(component)
        assert hit[0]['endpoint'] == ('Controlled_enter' if target else 'Controlled_exit')
        if target:
            assert r32(component + 0x38) == 1 and r32(component + 0x3c) == 0
            assert r32(component + 0x40) == 0 and r32(component + 0x44) == 173
        else:
            # Exit is called before new state0 is stored; execution stops there.
            assert r32(component + 0x38) == 1 and hit[0]['target'] == 0
        assert r32(component + 0xb8) == 1  # callback/command completion not executed
        counts['receiver_queue_fsm_to_callback_boundary'] = counts.get('receiver_queue_fsm_to_callback_boundary', 0) + 1
        rows.append(dict(group='receiver_queue_fsm_to_callback_boundary', case=i, target=target,
                         state=r32(component + 0x38), endpoint=hit[0]))

    out = dict(scope='whole selected receiver paths and actual queue->FSM until existing Controlled enter/exit callback; '
                     'invalid/empty ActorRef only; actual original SDK memset through main PLT GOT; '
                     'no scene/sender, valid-handle thread/lock retention or callback physics execution',
               counts=counts, mismatch=0, total=sum(counts.values()), cases=rows, native_calls=native_calls,
               sdk_binding=dict(original_sdk_symbol=symbols[0], mapped_base=hex(SDK),
                                main_plt='0x7103e99f10', got_cell='0x710576efa8', binding_in_ram_only=True),
               guard_inputs=[hex(BASE + guard) for guard in guards],
               function_stubs=0, sdk_stubs=0, plt_return_stubs=0, arbitrary_math_stubs=0,
               previous6071_recounted=False)
    (OUT / 'next_vehicle_emu.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(total=out['total'], counts=counts, mismatch=0, native_calls=native_calls)))


if __name__ == '__main__':
    main()
