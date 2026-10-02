#!/bin/sh
# [state] 이미 색인된 함수를 전체 분석 프로젝트(spl3_main)로 다시 디컴파일한다(full_decomp.sh 는 색인된 주소를 건너뛰므로).
# 사용: sh web/tools/state_redecomp.sh <출력.c> <함수시작...>   (잠금은 full_decomp.sh 와 같은 ghidra_proj/full_lock)
out="$1"; shift
R=c:/dev/splatoon3
export JAVA_HOME="C:/Program Files/Java/jdk-21"
export PATH="/c/Program Files/Java/jdk-21/bin:$PATH"
export GHIDRA_HEADLESS_MAXMEM=8G
export MSYS_NO_PATHCONV=1
until mkdir $R/ghidra_proj/full_lock 2>/dev/null; do sleep 5; done
log=$R/ghidra_proj/full_last_$$.log
c:/dev/mpj/tools/ghidra_12.1.2_PUBLIC/support/analyzeHeadless.bat $R/ghidra_proj spl3_main -process main.nso -noanalysis -readOnly \
  -scriptPath $R/web/tools/ghidra_scripts -postScript QuickDecomp.java "$out" "$@" > $log 2>&1
rmdir $R/ghidra_proj/full_lock
grep -E "decomp [0-9]+|ERROR|Exception" $log | head -5
rm -f $log
