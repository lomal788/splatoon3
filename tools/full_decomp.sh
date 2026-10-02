#!/bin/sh
# 사용: web/tools/full_decomp.sh <출력.c> <주소...>
# 전체 분석이 끝난 ghidra_proj/spl3_main 프로젝트로 디컴파일한다(함수 경계·타입 추론이 quick_decomp보다 정확).
# 원본 프로젝트 + 사본 f1, f2 로 3개까지 동시에 돈다(빈 슬롯 대기). 호출당 약 30초. 이미 색인된 주소는 건너뛴다.
out="$1"; shift
R=c:/dev/splatoon3
PY=$R/.venv/Scripts/python
$PY $R/web/tools/decomp_index.py --no-build "$@" | grep -v "디컴파일 없음" | sed 's/^/이미 있음: /'
todo=$($PY $R/web/tools/decomp_index.py --missing "$@")
if [ -z "$todo" ]; then echo "새로 디컴파일할 주소 없음"; exit 0; fi
export JAVA_HOME="C:/Program Files/Java/jdk-21"
export PATH="/c/Program Files/Java/jdk-21/bin:$PATH"
export GHIDRA_HEADLESS_MAXMEM=8G
export MSYS_NO_PATHCONV=1
until mkdir $R/ghidra_proj/full_lock 2>/dev/null; do sleep 5; done
log=$R/ghidra_proj/full_last_$$.log
c:/dev/mpj/tools/ghidra_12.1.2_PUBLIC/support/analyzeHeadless.bat $R/ghidra_proj spl3_main -process main.nso -noanalysis -readOnly \
  -scriptPath $R/web/tools/ghidra_scripts -postScript QuickDecomp.java "$out" $todo > $log 2>&1
rmdir $R/ghidra_proj/full_lock
grep -E "decomp [0-9]+|ERROR|Exception" $log | head -5
rm -f $log
$PY $R/web/tools/decomp_index.py
