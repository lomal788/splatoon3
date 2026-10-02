"""디컴파일 C 에서 파라미터 상속 조회 반복문(설정 플래그가 없으면 $parent 로 올라가는 while)을 한 줄 주석으로 접는다.
사용: PY web/tools/gfx4_fold.py <파일.c> [함수주소] > 출력
접힌 줄: /* INHERIT <변수> flag <식> */  — 뒤따르는 필드 읽기는 '설정된 조상'의 값이다.
"""
import re, sys
src = open(sys.argv[1], encoding='utf8', errors='replace').read().splitlines()
want = sys.argv[2].lower().replace('0x', '') if len(sys.argv) > 2 else None
out, keep = [], want is None
i = 0
while i < len(src):
    ln = src[i]
    if ln.startswith('// ==== '):
        keep = want is None or ln.split()[2].lower() == want
    if not keep:
        i += 1; continue
    m = re.match(r'^(\s*)if \(\(\*\(byte \*\)(.+?) & 1\) == 0\) \{\s*$', ln)
    if m:
        depth, j, body = 0, i, []
        while j < len(src):
            depth += src[j].count('{') - src[j].count('}')
            body.append(src[j])
            if depth == 0:
                break
            j += 1
        txt = '\n'.join(body)
        if '__cxa_guard_acquire' in txt and 'PTR_DAT_710553d070' in txt and 'while' in txt:
            var = re.search(r'\|\| \((\w+) = (\w+)', txt)
            out.append('%s/* INHERIT %s <- flag %s */' % (m.group(1), var.group(1) if var else '?', m.group(2)))
            i = j + 1; continue
    out.append(ln); i += 1
print('\n'.join(out))
