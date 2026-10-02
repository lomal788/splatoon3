"""nn::vfx 디컴파일(.c)에서 ResEmitter(이미터 바이너리) 오프셋 사용처를 모은다.

포인터 출처(판독):
  이미터 인스턴스 +0x250 = EmitterResource(0x470 B 런타임 객체, 0x710081aee4 가 채움)
  EmitterResource +0x10 = ResEmitter(파일 이미터 바이너리 시작), +0x18 = ResEmitter+0x70(정적 블록, GPU UBO 로 감)
  이미터 인스턴스 +0xb0 = ResEmitter (0x710080ca78 에서 복사)
지역 변수 별칭을 따라가며 `(VAR + 0xNNN)` 접근을 ResEmitter 기준 오프셋으로 모은다(정적 블록은 +0x70 보정).

사용: PY web/tools/vfx_resfield_scan.py <c파일...> [--off 0xNNN] [--min 0x70]
"""
import collections
import re
import sys

V = r'([a-zA-Z_][a-zA-Z_0-9]*)'


def scan(paths, only=None, mn=0x70):
    uses = collections.defaultdict(list)
    for p in paths:
        txt = open(p, encoding='utf-8', errors='replace').read()
        for blk in re.split(r'\n// ==== ', txt):
            m = re.match(r'([0-9a-f]+) ', blk)
            if not m:
                continue
            fn = '0x' + m.group(1)
            kind = {}  # var -> 'robj' | 'res' | 'st'
            for line in blk.split('\n'):
                # 표현식 정규화: 알려진 체인을 토큰으로 치환
                s = line
                for _ in range(3):
                    s = re.sub(r'\*\(long \*\)\(' + V + r' \+ 0x250\)', lambda mm: '@ROBJ', s)
                    s = re.sub(r'\*\(long \*\)\(@ROBJ \+ 0x10\)', '@RES', s)
                    s = re.sub(r'\*\(long \*\)\(@ROBJ \+ 0x18\)', '@ST', s)
                    s = re.sub(r'\*\(long \*\)\(' + V + r' \+ 0xb0\)', lambda mm: '@RES' if kind.get(mm.group(1)) != 'skip' else mm.group(0), s)
                    for var, k in kind.items():
                        tok = {'robj': '@ROBJ', 'res': '@RES', 'st': '@ST'}[k]
                        s = re.sub(r'\b' + var + r'\b(?! =)', tok, s)
                    s = re.sub(r'\*\(long \*\)\(@ROBJ \+ 0x10\)', '@RES', s)
                    s = re.sub(r'\*\(long \*\)\(@ROBJ \+ 0x18\)', '@ST', s)
                a = re.match(r'\s*' + V + r' = (@ROBJ|@RES|@ST);', s)
                if a:
                    kind[a.group(1)] = {'@ROBJ': 'robj', '@RES': 'res', '@ST': 'st'}[a.group(2)]
                    continue
                a = re.match(r'\s*' + V + r' = ', s)
                if a and a.group(1) in kind:
                    del kind[a.group(1)]
                for mm in re.finditer(r'\*\((\w+) \*\)\((@RES|@ST) \+ (0x[0-9a-f]+)\)', s):
                    off = int(mm.group(3), 16) + (0x70 if mm.group(2) == '@ST' else 0)
                    uses[off].append((mm.group(1), fn, line.strip()[:170]))
                for mm in re.finditer(r'\*\((\w+) \*\)(@RES|@ST)\b', s):
                    off = 0x70 if mm.group(2) == '@ST' else 0
                    uses[off].append((mm.group(1), fn, line.strip()[:170]))
    for off in sorted(uses):
        if off < mn or (only is not None and off != only):
            continue
        fns = collections.Counter(u[1] for u in uses[off])
        types = collections.Counter(u[0] for u in uses[off])
        print(f'+{off:#05x} {dict(types)} fns={dict(fns)}')
        if only is not None:
            for t, fn, line in uses[off]:
                print('   ', fn, line)


if __name__ == '__main__':
    args = sys.argv[1:]
    only = None
    mn = 0x70
    if '--off' in args:
        i = args.index('--off')
        only = int(args[i + 1], 16)
        del args[i:i + 2]
    if '--min' in args:
        i = args.index('--min')
        mn = int(args[i + 1], 16)
        del args[i:i + 2]
    scan(args, only, mn)
