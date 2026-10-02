#!/bin/sh
# [player] 큰 함수용(PlayerBigDecomp.java). 사용: web/tools/player_bigdecomp.sh <출력.c> <함수시작주소...>
# main.reloc.img를 분석 없이 raw로 올린 프로젝트에서 지정 함수만 즉석 디컴파일한다.
# - (quick_decomp.sh와 달리) 색인에 있어도 다시 디컴파일한다.
# - 프로젝트 사본 ghidra_proj/q0~q3 중 비어 있는 것을 잡아 쓰므로 4개까지 동시에 돌 수 있다.
# - 호출마다 프로젝트 로딩에 약 2분이 들므로 주소를 한 번에 여러 개 넘길 것.
# - 끝나면 색인을 갱신한다.
out="$1"; shift
R=c:/dev/splatoon3
PY=$R/.venv/Scripts/python
P=$R/ghidra_proj
todo="$*"
if [ -z "$todo" ]; then echo "새로 디컴파일할 주소 없음"; exit 0; fi
export JAVA_HOME="C:/Program Files/Java/jdk-21"
export PATH="/c/Program Files/Java/jdk-21/bin:$PATH"
export GHIDRA_HEADLESS_MAXMEM=8G
export MSYS_NO_PATHCONV=1
H=c:/dev/mpj/tools/ghidra_12.1.2_PUBLIC/support/analyzeHeadless.bat
slot=""
while [ -z "$slot" ]; do
  for i in 0 1 2 3; do
    if mkdir $P/q$i/lock 2>/dev/null; then slot=$i; break; fi
  done
  [ -z "$slot" ] && sleep 3
done
log=$P/q$slot/last_$$.log
$H $P/q$slot quick -process main.reloc.img -noanalysis -readOnly -scriptPath $R/web/tools/ghidra_scripts \
  -postScript PlayerBigDecomp.java "$out" $todo > $log 2>&1
rmdir $P/q$slot/lock
grep -E "decomp [0-9]+|failed|ERROR|Exception" $log | head -5
rm -f $log
$PY $R/web/tools/decomp_index.py
