"""Native readonly instruction/data audit. Not a runtime reachability proof."""
import json
import struct
from pathlib import Path
import numpy as np
from disasm import disasm
from xref import BASE, TEXT_END, load_img

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'


def main():
    data = load_img()
    words = np.frombuffer(data[:TEXT_END], dtype='<u4')
    rows = []
    for target in [0x249257c, 0x26744e0, 0x26b0bd4, 0x26b0ebc, 0x2530fe0]:
        indices = np.flatnonzero((words & 0xfc000000) == 0x94000000)
        immediates = (words[indices].astype(np.int64) & 0x3ffffff)
        immediates = np.where(immediates & 0x2000000, immediates - 0x4000000, immediates)
        calls = indices[indices * 4 + immediates * 4 == target]
        rows.append(dict(target=hex(BASE + target), direct_bl=[hex(BASE + int(c) * 4) for c in calls]))
    ranges = [(0x2471904, 0x2471974), (0x2493470, 0x24934f4),
              (0x2494360, 0x24943e0), (0x24944a0, 0x2494530),
              (0x2530fe0, 0x2531030), (0x24da0b0, 0x24da160)]
    assemblies = []
    for start, end in ranges:
        assemblies.append(dict(start=hex(BASE+start), end=hex(BASE+end),
                               rows=[dict(pc=hex(BASE+p), asm=a, annotation=n)
                                     for p, a, n in disasm(data, start, end=end)]))
    string_addresses = [0x493c1f5, 0x494d790, 0x48e0aa1, 0x4968b33]
    strings = []
    for address in string_addresses:
        end = data.find(b'\0', address, address+128)
        assert end >= address
        strings.append(dict(address=hex(BASE+address), text=data[address:end].decode('ascii')))
    grind = [struct.unpack_from('<Q', data, 0x5635660+i*8)[0] for i in [32, 34]]
    result = dict(scope='readonly original BL/instruction/string audit; no scene or event execution',
                  direct_calls=rows, assemblies=assemblies, pipeline_fsm_names=strings,
                  grind_vt100=hex(grind[0]), grind_vt110=hex(grind[1]),
                  typed_bindings=[dict(code=0x13, component_offset='0xa778', slot_offset='0xa1f0',
                                       component='spl::PlayerInkActionSpIkuraShoot', token='0x71058d6a28'),
                                  dict(code=0x16, component_offset='0xa790', slot_offset='0xa208',
                                       component='spl::PlayerInkActionSpGachihoko', token='0x71058d6858')])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'source_audit.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(direct_calls=rows, pipeline_fsm_names=strings,
                          output=str(OUT/'source_audit.json')), ensure_ascii=False))


if __name__ == '__main__':
    main()
