#!/bin/sh
# main NSO를 Ghidra 프로젝트(c:/dev/splatoon3/ghidra_proj/spl3_main)로 가져와 전체 분석 후 함수 목록을 내보낸다.
JAVA_HOME="C:/Program Files/Java/jdk-21" PATH="/c/Program Files/Java/jdk-21/bin:$PATH" GHIDRA_HEADLESS_MAXMEM=20G MSYS_NO_PATHCONV=1 c:/dev/mpj/tools/ghidra_12.1.2_PUBLIC/support/analyzeHeadless.bat \
  c:/dev/splatoon3/ghidra_proj spl3_main -import c:/dev/splatoon3/extracted/exefs/main.nso -overwrite \
  -scriptPath c:/dev/splatoon3/web/tools/ghidra_scripts -postScript ExportFunctions.java c:/dev/splatoon3/analysis/functions \
  > c:/dev/splatoon3/ghidra_proj/main_import.log 2>&1
