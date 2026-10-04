"""Readonly native PlayerDemo parameter/flag/timer correspondence and bounded scans."""
import json
import struct
from pathlib import Path

import numpy as np
from class_info import class_info, ptrs_to
from disasm import disasm
from r6_camweapon_seed_emu import tag_data
from xref import BASE, TEXT_END, load_idx, load_img

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'


def snapshot(data, start, end):
    return dict(start=hex(BASE+start), end=hex(BASE+end), rows=[
        dict(pc=hex(BASE+pc), asm=asm, annotation=note)
        for pc, asm, note in disasm(data, start, end=end)])


def main():
    data, idx = load_img(), load_idx()
    demo_class = class_info(data, idx, 'spl::PlayerDemo')
    demo_vt = int(demo_class['vtable'], 16)-BASE
    assert struct.unpack_from('<Q', data, demo_vt+16*8)[0] == BASE+0x23613ec
    assert struct.unpack_from('<Q', data, demo_vt+20*8)[0] == BASE+0x250b8f0
    params = []
    for name, vt, key, default, parser, isa, fields in [
        ('control_flags', 0x56228a0, 0x58b4218, 0x2363fe4, 0x2363ff4, 0x2367088,
         [('CanMove', 0x40), ('CanControlCamera', 0x41), ('CanDraw', 0x42)]),
        ('timed_direction', 0x5623020, 0x58b4288, 0x23655a0, 0x23655b8, 0x236bb14,
         [('IsSquid', 0x40), ('Dir', 0x44), ('Time', 0x50)]),
    ]:
        slots = struct.unpack_from('<11Q', data, vt)
        assert slots[2] == BASE+default and slots[8] == BASE+isa and slots[10] == BASE+parser
        params.append(dict(name=name, vtable=hex(BASE+vt), token=hex(BASE+key),
                           default=hex(BASE+default), parser=hex(BASE+parser), isa=hex(BASE+isa),
                           fields=[dict(name=field, offset=hex(off)) for field, off in fields],
                           slots=[hex(slot) for slot in slots]))
    words = np.frombuffer(data[:TEXT_END], dtype='<u4')
    # Exact instruction forms only: alias, pair/memset/copy stores remain possible.
    bf4_str = np.flatnonzero(((words & 0xffc00000) == 0xbd000000) &
                            (((words >> 10) & 0xfff) == 0xbf4//4))*4
    flag_mov = np.flatnonzero(((words & 0x7f800000) == 0x52800000) &
                             (((words >> 5) & 0xffff) == 0x9213))*4
    assert [int(pc) for pc in bf4_str] == [0x2361cf4, 0x250b9a4]
    assert len(flag_mov) == 31 and 0x24cbefc in flag_mov
    tag_rows, tag_names, tag_bits = tag_data()
    tag_col = tag_names.index('Scene_Versus')
    assert tag_col == 160
    lobby_row = next(i for i, row in enumerate(tag_rows)
                     if row[:2] == ['Work/Scene/', 'LobbyVersus'])
    bit_index = lobby_row * len(tag_names) + tag_col
    lobby_bit = (tag_bits[bit_index >> 3] >> (bit_index & 7)) & 1
    assert lobby_row == 4272 and lobby_bit == 0
    ranges = [(0x250b2a0, 0x250b2e0), (0x23613ec, 0x23614dc),
              (0x2361c70, 0x2361cf8), (0x250b8f0, 0x250b9f8),
              (0x2363fe4, 0x2364294), (0x23655a0, 0x2365838),
              (0x2367088, 0x23670e8), (0x236bb14, 0x236bb74),
              (0x24cbef0, 0x24cbf28), (0x24cbb08, 0x24cbb38),
              (0x2457fd0, 0x2458098), (0x2458180, 0x24581e0),
              (0x309d440, 0x309d4cc), (0x30aa0cc, 0x30aa160),
              (0x2500fe4, 0x2501034), (0x2500e60, 0x2500ebc),
              (0x24e2d80, 0x24e2eb0), (0x24e407c, 0x24e414c),
              (0x24e42f8, 0x24e4394), (0x2c85040, 0x2c850b8),
              (0x345f99c, 0x345fa20), (0x347a2c8, 0x347a348)]
    result = dict(scope='parameter VT/name/field mapping, selected native snapshots and exact-form scans only. '
                        'No all-writer absence, script source, scene or mode gameplay claim.',
                  classes=[demo_class, class_info(data, idx, 'spl::PlayerCoopSeq'),
                           class_info(data, idx, 'SplVersusReady'),
                           class_info(data, idx, 'SplVersusResultSelector')],
                  parameters=params,
                  commands=[dict(id='0x6e9f8200', key='0x71058b4218', fields='payload40/41/42 -> Demo33/34/35'),
                            dict(id='0x6e9f8201', fields='activeDemo30 -> clear30/set33..36=1'),
                            dict(id='0x6e9f8228', key='0x71058b4288', fields='payloadDir/IsSquid/Time -> be4/bf8/bf4')],
                  direct_str_s_bf4=[hex(BASE+int(pc)) for pc in bf4_str],
                  movz_9213_candidates=[hex(BASE+int(pc)) for pc in flag_mov],
                  result_flag_store='0x71024cbf08', result_flag_callback='0x71024cbcb8',
                  lobby_versus_tag=dict(source='extracted/romfs/RSDB/Tag.Product.100.rstbl.byml.zs',
                                        existing_evidence='SHARED.md lines245/520 and r6 seed evidence; not new execution',
                                        row=lobby_row, path=tag_rows[lobby_row], tag=tag_names[tag_col],
                                        tag_column=tag_col, bit=lobby_bit),
                  coop_signal=dict(component='spl::PlayerCoopSeq', input_field='component+0x1348',
                                   subscription_node='component+0x1370', key='0x7105861808',
                                   callback='0x7102500fe4', copy='message+0x18 u32 -> component+0x1348',
                                   queued_vtable='0x71056830c0', producer_literal13='0x7102c850ac',
                                   camera_compares_literal12='0x71024e40ec',
                                   enum16_name='spl::CoopSequenceSignalType',
                                   enum16_reader='0x7103499284', enum16_result_index=12,
                                   enum12_registration='0x71027b3ab4', enum12_result_index=11,
                                   unresolved='Typed association between queued key5861808 field+18 and enum16 descriptor. '
                                              'Do not assign Result to raw12 from adjacent string only.'),
                  callback_ptrs={hex(BASE+t): [hex(BASE+p) for p in ptrs_to(data, BASE+t)]
                                  for t in [0x2500fe4, 0x24cb4cc, 0x24cbcb8]},
                  assemblies=[snapshot(data, start, end) for start, end in ranges])
    (OUT/'demo_source_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(parameters=len(params), direct_str_s_bf4=result['direct_str_s_bf4'],
                         movz_9213_candidates=len(flag_mov), result_flag_store=result['result_flag_store'])))


if __name__ == '__main__':
    main()
