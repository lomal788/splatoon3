"""r5 ui: 전 레이아웃 BFLAN 의 user(FLEU) 애니 엔트리가 가리키는 사용자 데이터 이름을 모은다.

엔트리 구조(관측): name[28], ntag u8, target u8(2=user), pad u16, 태그 오프셋 u32[ntag],
target==2 이면 이어서 이름 오프셋 u32[ntag](엔트리 기준) → (u32 4 + 문자열).
출력: 이름별 개수, 태그 수, 이름 없는 엔트리 수.
"""
import glob, struct, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ui_sarc  # noqa

def scan(b, stats, where):
    i = b.find(b'pai1')
    if i < 0:
        return
    fsize, loop, ntex, nent, etab = struct.unpack_from('<HBxHHI', b, i + 8)
    for eo in struct.unpack_from(f'<{nent}I', b, i + etab):
        e = i + eo
        ntag, target = b[e + 28], b[e + 29]
        if target != 2:
            continue
        toffs = struct.unpack_from(f'<{ntag}I', b, e + 32)
        noffs = struct.unpack_from(f'<{ntag}I', b, e + 32 + 4 * ntag)
        for to, no in zip(toffs, noffs):
            t = e + to
            tagname = b[t + 4:t + 8]
            p = e + no
            rel = struct.unpack_from('<I', b, p)[0]
            s = b[p + rel:p + rel + 64].split(b'\0')[0].decode('ascii', 'replace')
            stats['tags'][tagname.decode()] += 1
            stats['names'][s] += 1
            stats['n'] += 1

def main():
    stats = {'tags': collections.Counter(), 'names': collections.Counter(), 'n': 0}
    for f in sorted(glob.glob('extracted/romfs/Layout/*.blarc.zs')):
        files = ui_sarc.read_files(f)
        for name, data in files.items():
            if name.endswith('.bflan'):
                scan(data, stats, f + ':' + name)
    print('user 태그 수', stats['n'])
    print('태그 종류', dict(stats['tags']))
    print('이름', dict(stats['names']))

if __name__ == '__main__':
    main()
