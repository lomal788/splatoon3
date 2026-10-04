// 담당: [physics] — Phive 접촉 목록 정리 0x7103a6144c. 모드 3 = 키 f 오름차순 1-기반 최대 힙 정렬(불안정) [실행 3000/3000].
// 근거: docs/physics/phive_controller.md 6차 갱신 표("접촉 정리 0x7103a6144c 정렬 기준"), web/tools/r6_physics_contactsort_emu.py.

/**
 * 모드 3 정렬. key(C) = (C+0x68 & 0x1060) ? C+0x60(비율 f) : 0. 같은 키의 순서는 원본 힙 순서 그대로다.
 * 용량 조건(count − 1 < cap)이 맞지 않으면 원본처럼 그대로 둔다.
 */
export function heapSortMode3<T>(items: T[], key: (x: T) => number, cap = items.length): T[] {
  const a = items.slice();
  const n = a.length;
  if (n < 2 || !(n - 1 < cap)) return a;
  const A = (i: number): T => a[i - 1];
  let j = n >> 1;
  for (;;) {
    const v = a[j - 1];
    let pos = j, c2 = 2 * j;
    while (c2 <= n) {
      let c = c2;
      if (c2 < n && key(A(c2)) < key(A(c2 + 1))) c = c2 + 1;
      if (key(A(c)) <= key(v)) break;
      a[pos - 1] = A(c);
      pos = c;
      c2 = 2 * c;
    }
    a[pos - 1] = v;
    if (j <= 1) break;
    j--;
  }
  let last = n - 1;
  let v = a[last];
  a[last] = a[0];
  let m = n;
  while (m > 2) {
    const heap = m - 1;
    let pos = 1, c2 = 2;
    for (;;) {
      let c = c2;
      if (c2 < heap && key(A(c2)) < key(A(c2 + 1))) c = c2 + 1;
      if (key(A(c)) <= key(v)) break;
      a[pos - 1] = A(c);
      pos = c;
      c2 = 2 * c;
      if (!(c2 < m)) break;
    }
    a[pos - 1] = v;
    last--;
    v = a[last];
    a[last] = a[0];
    m--;
  }
  a[0] = v;
  return a;
}
