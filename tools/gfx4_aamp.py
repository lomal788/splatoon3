"""render_aamp.dump 에 gfx4_aamp_names.py 가 찾은 이름 사전(analysis/gfx4/aamp_names.txt)을 더해 덤프.
사용: PY web/tools/gfx4_aamp.py <파일.bagl*|.bgenv>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_aamp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NF = os.path.join(ROOT, "analysis/gfx4/aamp_names.txt")

if __name__ == "__main__":
    extra = open(NF, encoding="utf8").read().split() if os.path.exists(NF) else []
    for f in sys.argv[1:]:
        if len(sys.argv) > 2:
            print("=====", f)
        print("\n".join(render_aamp.dump(f, extra)))
