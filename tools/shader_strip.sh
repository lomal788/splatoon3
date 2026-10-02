#!/bin/sh
# 역번역 GLSL 에서 temp 선언·확장·support_buffer/RegisterUBO 선언부를 빼고 본문만 출력
for f in "$@"; do
  echo "=== $f"
  grep -v -E "^\s+(precise )?(float|vec[234]|int|uint|bool|ivec[234]|uvec[234]) temp_[0-9]+;$" "$f" \
    | grep -v -E "^#extension|^#pragma|^const int undef|^#version|^\s*$" \
    | sed '/_support_buffer/,/} support_buffer;/d' | sed '/uniform _RegisterUBO/,/} RegisterUBO;/d'
done
