"""Native PlayerDemo typed camera-control/timed-dir supply, bounded empty queue.

Actual parameter VTables/IsA and complete receiver selected command paths run.
Ready guards/global objects are synthetic inputs; no function/SDK/math stubs.
Does not run script producers, scenes, allocator construction or queued commands.
"""
import json
import random
import struct
from pathlib import Path

import numpy as np
from unicorn import UC_HOOK_CODE
from network_uc import UC, BASE, STUB

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'


def fvalue(bits):
    return np.frombuffer(struct.pack('<I', bits), dtype='<f4')[0]


def fbits(value):
    return int(np.asarray([value], dtype='<f4').view('<u4')[0])


def main():
    uc = UC()
    mu = uc.mu
    rng = random.Random(101037)
    demo = uc.alloc(0xce8)
    payload = uc.alloc(0x100)
    msg = uc.alloc(0x20)
    global_obj = uc.alloc(0x200)
    body = uc.alloc(0xb000)
    behavior = uc.alloc(0x120)
    table = uc.alloc(8 * 0xd0)
    table_header = uc.alloc(0x20)
    names = uc.alloc(8 * 64)
    mu.mem_write(BASE + 0x580dec0, struct.pack('<Q', global_obj))
    mu.mem_write(behavior + 0x108, struct.pack('<Q', body))
    guard_inputs = [0x58b4220, 0x58b4290, 0x5800d90]
    for guard in guard_inputs:
        mu.mem_write(BASE + guard, b'\x01')
    calls = {'0x7102367088': 0, '0x710236bb14': 0}
    rows = []
    counts = {}

    def audit(m, address, size, _):
        if STUB <= address < STUB + 0x1000 or BASE+0x3e90000 <= address < BASE+0x3e9e000:
            raise AssertionError(('unexpected function stub/PLT', hex(address)))
        if hex(address) in calls:
            calls[hex(address)] += 1

    mu.hook_add(UC_HOOK_CODE, audit)

    def record(group, inputs, output):
        counts[group] = counts.get(group, 0) + 1
        rows.append(dict(group=group, inputs=inputs, output=output))

    # Actual parameter defaults; constructors allocating the outer object not run.
    for kind, fn, expected in [
        ('control', 0x2363fe4, {0x40: b'\0\0\1'}),
        ('timed_dir', 0x23655a0, {0x40: b'\0', 0x44: struct.pack('<4I', 0, 0, 0x3f800000, 0xbf800000)}),
    ]:
        mu.mem_write(payload, b'\xa5' * 0x100)
        uc.call(BASE+fn, payload)
        for off, raw in expected.items():
            assert bytes(mu.mem_read(payload+off, len(raw))) == raw, (kind, off)
        record('parameter_defaults', dict(kind=kind), {hex(off): raw.hex() for off, raw in expected.items()})

    specs = [
        ('control', 0x2363fe4, 0x2363ff4,
         {'CanMove': (0x40, 1), 'CanControlCamera': (0x41, 1), 'CanDraw': (0x42, 1)}),
        ('timed_dir', 0x23655a0, 0x23655b8,
         {'IsSquid': (0x40, 1), 'Dir': (0x44, 12), 'Time': (0x50, 4)}),
    ]
    # Complete native parsers: literal names, duplicates, missing names, bounds.
    for kind, default_fn, parser_fn, fields in specs:
        for i in range(64):
            n = i % 8
            capacity = [0, 1, n][(i // 8) % 3]
            entries = []
            for j in range(n):
                name = rng.choice(list(fields)+['Unknown', 'TimeExtra', 'canMove'])
                raw = rng.randbytes(12)
                entry = table + j * 0xd0
                name_ptr = names + j * 64
                # Parser explicitly writes the last byte to zero, as in original.
                encoded = name.encode('ascii') + b'X'
                mu.mem_write(name_ptr, encoded)
                mu.mem_write(entry, b'\0' * 0xd0)
                mu.mem_write(entry+0x10, struct.pack('<Qi', name_ptr, len(encoded)))
                mu.mem_write(entry+0xa0, raw)
                entries.append((name, raw))
            mu.mem_write(table_header, struct.pack('<I4xQi', capacity, table, n))
            mu.mem_write(payload, b'\xa5'*0x100)
            uc.call(BASE+default_fn, payload)
            expected = bytearray(mu.mem_read(payload, 0x100))
            for j in range(n):
                name, raw = entries[j if j < capacity else 0]
                if name in fields:
                    off, size = fields[name]
                    expected[off:off+size] = raw[:size]
            uc.call(BASE+parser_fn, payload, table_header)
            actual = bytes(mu.mem_read(payload, 0x100))
            assert actual == bytes(expected), (kind, i, actual.hex(), bytes(expected).hex())
            record('parameter_parser_'+kind, dict(count=n, capacity=capacity,
                   names=[name for name, _ in entries]), actual[0x40:0x54].hex())

    # Selected whole receiver paths, actual matching and nonmatching payload RTTI.
    for i in range(192):
        initial = bytearray(rng.randbytes(0xce8))
        initial[0x48:0x4c] = b'\0'*4
        old_active = [0, 1, 255][i % 3]
        initial[0x30] = old_active
        initial[0xc60:0xc68] = struct.pack('<Q', behavior)
        disabled = [0, 1][(i // 3) % 2]
        command = [0x6e9f8200, 0x6e9f8201][(i // 6) % 2]
        payload_kind = ['match', 'wrong', 'null'][(i // 12) % 3]
        flags = bytes(rng.choice([0, 1, 255]) for _ in range(3))
        payload_vt = 0x56228a0 if payload_kind == 'match' else 0x5623020
        mu.mem_write(payload, b'\0'*0x100)
        mu.mem_write(payload, struct.pack('<Q', BASE+payload_vt))
        mu.mem_write(payload+0x40, flags)
        mu.mem_write(msg, struct.pack('<II8xQ', 0, command, 0 if payload_kind == 'null' else payload))
        mu.mem_write(global_obj+0x1a9, bytes([disabled]))
        mu.mem_write(demo, bytes(initial))
        expected = bytearray(initial)
        result = 1
        if command == 0x6e9f8200:
            if payload_kind != 'match':
                result = 0
            elif not disabled:
                expected[0x30] = 1
                expected[0x31] = 0
                expected[0x33:0x36] = flags
        elif not disabled and old_active:
            expected[0x30] = 0
            expected[0x33:0x37] = b'\1'*4
        actual_ret = uc.call(BASE+0x23613ec, demo, msg) & 0xffffffff
        actual = bytes(mu.mem_read(demo, 0xce8))
        assert actual_ret == result and actual == bytes(expected), ('control receiver', i, actual_ret, result)
        record('receiver_control', dict(id=hex(command), disabled=disabled, payload_kind=payload_kind,
                   old_active=old_active, flags=flags.hex()), actual[0x30:0x38].hex())

    time_bits = [0, 0x80000000, 1, 0x80000001, 0x3c888889, 0x3f800000,
                 0xbf800000, 0x7f7fffff, 0x7f800000, 0xff800000, 0x7fc12345, 0x7f812345]
    height_bits = [0, 0x80000000, 0x3dcccccd, 0x3f800000, 0x7fc12345, 0xff800000]
    for tb in time_bits:
        for hb in height_bits:
            for squid in [0, 1, 255]:
                initial = bytearray(rng.randbytes(0xce8))
                initial[0x48:0x4c] = b'\0'*4
                initial[0xc60:0xc68] = struct.pack('<Q', behavior)
                mu.mem_write(demo, bytes(initial))
                mu.mem_write(body+0xd3c, struct.pack('<I', hb))
                direction = rng.randbytes(12)
                mu.mem_write(payload, struct.pack('<Q', BASE+0x5623020))
                mu.mem_write(payload+0x40, bytes([squid]))
                mu.mem_write(payload+0x44, direction)
                mu.mem_write(payload+0x50, struct.pack('<I', tb))
                mu.mem_write(msg, struct.pack('<II8xQ', 0, 0x6e9f8228, payload))
                expected = bytearray(initial)
                expected[0xbe4:0xbf0] = direction
                # Original FMAX, not FMAXNM: quiet/propagate the source NaN.
                max_bits = (hb | 0x400000) if np.isnan(fvalue(hb)) else fbits(max(fvalue(hb), fvalue(0x3e99999a)))
                expected[0xbf0:0xbf4] = struct.pack('<I', max_bits)
                expected[0xbf8] = squid
                target_tb = 0x7f7fffff if fvalue(tb) < 0 else tb
                expected[0xbf4:0xbf8] = struct.pack('<I', target_tb)
                actual_ret = uc.call(BASE+0x23613ec, demo, msg) & 0xffffffff
                actual = bytes(mu.mem_read(demo, 0xce8))
                assert actual_ret == 1 and actual == bytes(expected), ('timed receiver', hex(tb), hex(hb), squid)
                record('receiver_timed_dir', dict(time_bits=hex(tb), height_bits=hex(hb), IsSquid=squid),
                       actual[0xbe4:0xbf9].hex())

    # Complete empty-queue tick, including expiry overlap writes and signed Bad0.
    old_timers = time_bits + [0x3c888888, 0x3d088889, 0x3e99999a, 0x40a00000]
    for tb in old_timers:
        for squid in [0, 1, 255]:
            for bad0 in [-2, -1, 0, 1, 2, 3, 0x7fffffff, -0x80000000]:
                initial = bytearray(rng.randbytes(0xce8))
                initial[0x48:0x4c] = b'\0'*4
                initial[0xc60:0xc68] = struct.pack('<Q', behavior)
                initial[0xbf4:0xbf8] = struct.pack('<I', tb)
                initial[0xbf8] = squid
                expected = bytearray(initial)
                expected[0x32] = 0
                new_bad0 = bad0
                if fvalue(tb) > 0:
                    new = np.float32(fvalue(tb) + fvalue(0xbc888889))
                    expected[0xbf4:0xbf8] = struct.pack('<I', fbits(new))
                    if new <= 0:
                        expected[0xbe4:0xbf9] = b'\0' * 21
                    else:
                        if squid:
                            expected[0x32] = 1
                        if bad0 <= 1:
                            new_bad0 = 2
                mu.mem_write(demo, bytes(initial))
                mu.mem_write(body+0xad0, struct.pack('<i', bad0))
                uc.call(BASE+0x250b8f0, demo)
                actual = bytes(mu.mem_read(demo, 0xce8))
                actual_bad0 = struct.unpack('<i', mu.mem_read(body+0xad0, 4))[0]
                assert actual == bytes(expected) and actual_bad0 == new_bad0, ('tick', hex(tb), squid, bad0)
                record('empty_queue_tick', dict(timer_bits=hex(tb), IsSquid=squid, Bad0=bad0),
                       dict(fields=actual[0xbe4:0xbf9].hex(), flag32=actual[0x32], Bad0=actual_bad0))

    result = dict(scope='parameter defaults/parsers; whole selected receiver commands; whole empty-queue tick. '
                        'Synthetic global/actor/message input; no script producers, construction or scene run.',
                  counts=counts, mismatch=0, guard_inputs=[hex(BASE+g) for g in guard_inputs],
                  native_calls=calls, function_stubs=0, sdk_stubs=0, plt_stubs=0,
                  arbitrary_math_stubs=0, stub_calls=[], cases=rows)
    (OUT/'demo_results.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(counts=counts, mismatch=0, native_calls=calls, stubs=0)))


if __name__ == '__main__':
    main()
