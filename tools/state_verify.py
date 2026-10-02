"""상태 표(0x7105630270)의 애니 이름이 ASB 커맨드 이름과 맞는지 데이터 대조.
사용: PY web/tools/state_verify.py
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import importlib.util
def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), name + '.py'))
    m = importlib.util.module_from_spec(spec)
    old = sys.argv; sys.argv = [name, '--md']
    try:
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(m)
    finally:
        sys.argv = old
    return m
st = _load('state_table')
asb = _load('state_asb')
R = 'C:/dev/splatoon3/extracted/actor/SplPlayer/AS/'
hum = {c['name'] for c in asb.load(R + 'SplPlayer.root.asb')['commands']}
sq = {c['name'] for c in asb.load(R + 'SplPlayerSquid.root.asb')['commands']}
miss = []; ok = 0
used_h, used_s = set(), set()
for i in range(st.N):
    w = [st.u64(st.BASE + i * 32 + j * 8) for j in range(4)]
    hn, sn = st.cstr(w[0]), st.cstr(w[1])
    if hn:
        used_h.add(hn)
        (ok := ok + 1) if hn in hum else miss.append((hex(i), 'human', hn))
    elif sn:
        used_s.add(sn)
        (ok := ok + 1) if sn in sq else miss.append((hex(i), 'squid', sn))
    else:
        miss.append((hex(i), 'none', ''))
print('상태', st.N, '일치', ok, '불일치', len(miss))
for m in miss: print('  ', m)
print('사람 ASB 커맨드', len(hum), '중 상태표가 안 쓰는 것:', sorted(hum - used_h))
print('오징어 ASB 커맨드', len(sq), '중 상태표가 안 쓰는 것:', sorted(sq - used_s))
