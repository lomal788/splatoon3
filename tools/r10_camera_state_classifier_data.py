"""Original enum-string/WeaponSp RTTI/classifier correspondence, not gameplay."""
import json
import struct
from pathlib import Path
from class_info import class_info
from disasm import disasm
from xref import BASE, load_idx, load_img, refs_to

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'
TOKENS = [0x58d7480, 0x58d7620, 0x58d6958, 0x58d72e0, 0x58d6ed0, 0x58d6af8,
          0x58d6fa0, 0x58d6a28, 0x58d7140, 0x58d6508, 0x58d6858, 0x58d6e00,
          0x58d6d30, 0x58d76f0, 0x58d6668, 0x58d7210, 0x58d73b0, 0x58d7550, 0x58d6788]
CODE_SETUPS = [0x24936c8, 0x2493754, 0x24937c8, 0x24946e0, 0x2493878,
               0x24938cc, 0x2493918, 0x249439c, 0x249442c, 0x24944a8,
               0x24944e4, 0x2494618, 0x24947fc, 0x24948bc, 0x2494914,
               0x2494a00, 0x2494a50, 0x2494a9c, 0x2494ad4]
WRITERS = [0x24936cc, 0x2493758, 0x24937d0, 0x24946e8, 0x2493880, 0x249391c,
           0x249391c, 0x24943a4, 0x2494434, 0x249391c, 0x24944f0, 0x2494620,
           0x2494804, 0x24948c4, 0x249491c, 0x2494a08, 0x2494a58, 0x2494ad8, 0x2494ad8]


def main():
    data, idx = load_img(), load_idx()
    enum_address = data.find(b'NoSpecial, FullGauge, SuperShot, UltraShot, GreatBarrier,')
    assert enum_address == 0x4960049
    enum_text = data[enum_address:data.index(b'\0', enum_address)].decode('ascii')
    labels = enum_text.split(', ')
    assert len(labels) == 21
    table = []
    for enum_index, (name, token, writer, setup) in enumerate(zip(labels[2:], TOKENS, WRITERS, CODE_SETUPS), start=2):
        info = class_info(data, idx, 'spl::WeaponSp'+name)
        assert 'vtable' in info, info
        vt = int(info['vtable'],16)-BASE
        rtti = struct.unpack_from('<Q',data,vt)[0]-BASE
        rows = disasm(data,rtti,end=rtti+80)
        assert any(f'-> {hex(BASE+token)}' in n for _,_,n in rows), (name,hex(rtti))
        writer_rows = disasm(data,writer-20,end=writer+4)
        assert writer_rows[-1][1] == 'str w8, [x22, #0xd4]', writer_rows[-1]
        setup_row = disasm(data,setup,end=setup+4)[0]
        assert setup_row[1] == f'mov w8, #0x{10+enum_index:x}', setup_row
        table.append(dict(enum_index=enum_index, label=name, runtime_code=10+enum_index,
                          token=hex(BASE+token), writer=hex(BASE+writer), actor=info,
                          code_setup=dict(pc=hex(BASE+setup),asm=setup_row[1]),
                          actor_IsA=hex(BASE+rtti),
                          actor_IsA_prefix=[dict(pc=hex(BASE+p),asm=a,annotation=n) for p,a,n in rows],
                          writer_prefix=[dict(pc=hex(BASE+p),asm=a,annotation=n) for p,a,n in writer_rows]))
    classifier_ranges = [(0x2493330,0x249349c), (0x249368c,0x24936d0),
                         (0x24938f8,0x2493938), (0x2494320,0x24943b0),
                         (0x2494a70,0x2494ae0), (0x2494b8c,0x2494ba0)]
    result = dict(scope='native string-order/actual actor RTTI/classifier write correspondence; '
                        'no special gameplay or full classifier execution',
                  enum_string=dict(address=hex(BASE+enum_address),text=enum_text,
                                   positional_labels=labels,
                                   native_refs=[dict(address=hex(BASE+p),kind=k) for p,k in refs_to(enum_address,idx)]),
                  table=table, fallback=dict(writer='0x7102494b94',runtime_code=0),
                  unresolved='Other B65c writers and all runtime states not proved absent',
                  classifier_snapshots=[dict(start=hex(BASE+a),end=hex(BASE+b),
                    rows=[dict(pc=hex(BASE+p),asm=s,annotation=n) for p,s,n in disasm(data,a,end=b)])
                    for a,b in classifier_ranges])
    (OUT/'classifier_data.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(enum_address=hex(BASE+enum_address),labels=len(labels),
                          matched_actor_tokens=len(table),codes=[r['runtime_code'] for r in table]),
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
