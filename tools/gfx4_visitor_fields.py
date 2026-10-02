"""파라미터 방문 함수 디컴파일(.c)에서 (필드 이름, 값 오프셋, 설정 플래그 오프셋, 기본값 주소)를 뽑는다.
사용: PY web/tools/gfx4_visitor_fields.py <파일.c>
패턴(첫 번째 형 방문 함수): lStack = param_1 + OFF; ... local = param_1 + FLAG; ... local_88 = "Name"; ... local_58 = &DAT_xxx(기본값)
"""
import re, struct, sys
IMG = r'C:/dev/splatoon3/extracted/exefs/main.reloc.img'
m = open(IMG, 'rb').read(); B = 0x7100000000
src = open(sys.argv[1], encoding='utf8', errors='replace').read()
for fn in re.split(r'\n// ==== ', src):
    head = fn.split('\n', 1)[0]
    names = list(re.finditer(r'= "([A-Za-z0-9_]+)";', fn))
    if not names:
        continue
    print('==', head)
    prev = 0
    for mt in names:
        seg = fn[prev:mt.end() + 400]
        seg_before = fn[prev:mt.start()]
        offs = re.findall(r'= (?:\(\w+ \*?\))?param_1 \+ (0x[0-9a-f]+|\d+);', seg_before)
        offs2 = re.findall(r'= \(\w+ \*\)\(\(long\)param_1 \+ (0x[0-9a-f]+)\)', seg_before) + re.findall(r'= param_1 \+ (0x[0-9a-f]+|\d+)', seg_before)
        dflt = re.findall(r'= &DAT_([0-9a-f]+);', fn[mt.end():mt.end() + 300])
        vt = re.findall(r'= &PTR_FUN_([0-9a-f]+);', seg_before)
        o = offs[-2:] if len(offs) >= 2 else offs
        dv = ''
        if dflt:
            a = int(dflt[0], 16)
            try:
                dv = '%g' % struct.unpack_from('<f', m, a - B)[0]
            except Exception:
                pass
        print('  %-28s offs=%s vt=%s default@%s %s' % (mt.group(1), o, vt[-1:] , dflt[:1], dv))
        prev = mt.end()
