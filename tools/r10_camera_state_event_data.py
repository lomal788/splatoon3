"""Read-only original request/class/channel audit; no event delivery claim."""
import json
import struct
from pathlib import Path

from class_info import class_info, ptrs_to
from disasm import disasm
from xref import BASE, load_idx, load_img

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'


def main():
    data, idx = load_img(), load_idx()
    names = ['spl::GateManhole', 'spl::MissionGateway',
             'SplVersusBeforeGameSelector', 'SplVersusGameEndSelector', 'SplVersusFreeTest']
    infos = [class_info(data, idx, name) for name in names]
    for info, callback in zip(infos[:2], [0x215363c, 0x21b9c8c]):
        vt = int(info['vtable'], 16) - BASE
        assert struct.unpack_from('<Q', data, vt + 22 * 8)[0] == BASE + callback
        info['slot22_request_callback'] = hex(BASE + callback)
    mapping = [dict(field='B9210/B9214', node='Baa18', token='0x71058963e8',
                    callback='0x71024cb3ec', thunk='0x71024cc16c',
                    key_getter='0x71030894e0', type_test='0x710308937c',
                    generated_by_node='SplVersusBeforeGameSelector', enqueue_pc='0x71030831ac'),
               dict(field='B9212', node='Bab78', token='0x7105853238',
                    callback='0x71024cbca8', thunk='0x71024cc404',
                    key_getter='0x71030942fc', type_test='0x7103094198',
                    generated_by_node='SplVersusGameEndSelector', enqueue_pc='0x7103093910'),
               dict(field='B9210/B9211 clear; B9214 clear', node='Ba9c0', token='0x7105896978',
                    callback='0x71024cb3d4', generated_by_node='SplVersusFreeTest',
                    enqueue_pc='0x710308a0fc')]
    wrong_next = dict(node='Babd0', callback='0x71024cbcb8', token='0x71058bc348',
                      generated_by_node='SplVersusResultSelector',
                      warning='Adjacent node; not the B9210/B9212 subscription key.')
    channel_vtables = []
    for vt, type_test, getter in [(0x56aceb0, 0x308937c, 0x30894e0),
                                  (0x56ad828, 0x3094198, 0x30942fc)]:
        slots = struct.unpack_from('<5Q', data, vt)
        assert slots[:2] == (BASE + type_test, BASE + getter)
        channel_vtables.append(dict(vtable=hex(BASE+vt),
                                    slots=[hex(value) for value in slots],
                                    asserted_type_test=hex(BASE+type_test),
                                    asserted_key_getter=hex(BASE+getter)))
    ranges = [(0x215363c, 0x215369c), (0x215377c, 0x2153890),
              (0x2153974, 0x2153ac8), (0x21b9c8c, 0x21b9d08),
              (0x21b9ee8, 0x21b9fcc), (0x2457f48, 0x2458040),
              (0x2458120, 0x24581d8), (0x2352fdc, 0x2353054),
              (0x3089364, 0x30893a0), (0x3094178, 0x30941c4),
              (0x308a8e8, 0x308a924), (0x3083158, 0x30831cc),
              (0x30938c8, 0x3093930), (0x308a0b4, 0x308a11c),
              (0x24cb3d4, 0x24cb3ec)]
    assembly = [dict(start=hex(BASE + start), end=hex(BASE + end),
                     rows=[dict(pc=hex(BASE+p), asm=a, annotation=n)
                           for p, a, n in disasm(data, start, end=end)]) for start, end in ranges]
    point_name = struct.unpack_from('<Q', data, 0x56123d8)[0] - BASE
    string = data[point_name:data.index(b'\0', point_name)].decode('ascii')
    assert string == 'player_point'
    result = dict(scope='readonly instruction/type/name/VTable correspondence; queued-message '
                        'delivery and whole scene not executed', classes=infos,
                  registered_channel_mapping=mapping, adjacent_channel=wrong_next,
                  actual_channel_vtables=channel_vtables,
                  request_named_transform=dict(native_string=hex(BASE+point_name),
                                               record='0x71056123d8', name=string),
                  request_callback_ptrs={hex(BASE+t): [hex(BASE+p) for p in ptrs_to(data, BASE+t)]
                                         for t in [0x215363c, 0x21b9c8c]},
                  queue=dict(singleton='0x710582b7c0', allocator_offset='0xd0',
                             tail='0xe0', mutex='0x108', allocation_bytes=32,
                             linked_object_vptr_offset=8, delivery='unresolved'),
                  assemblies=assembly)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'event_source_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',
                                               encoding='utf-8')
    print(json.dumps(dict(classes=infos, mapping=mapping, adjacent=wrong_next), ensure_ascii=False))


if __name__ == '__main__':
    main()
