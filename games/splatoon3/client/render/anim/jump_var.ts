// Blackboard JumpVarID writer 0x710244128c (anim_state_machine.md §4.6).
/** 0x710244128c JumpVarID for a new state S in 0x99..0xa9 (anim_state_machine.md §4.6) [판독].
 * Body+0x1054 is taken as 0 (speed path) and the S==0x9a && SM+0x200<0x5b → 0 clause is unsupplied: both [미확정]. */
export function nativeJumpVarId(previous: number, prevState: number, s: number, speed: number, weaponKindMasked: boolean): number {
  if (speed <= 0.03) return 0;
  if (weaponKindMasked) return 0;
  const inR = (x: number, a: number, b: number): boolean => x >= a && x <= b;
  const c = prevState;
  let keep: boolean;
  if (c === 0x99 || c === 0x9a) keep = s === 0x99 || s === 0x9a || inR(s, 0x9b, 0x9f);
  else if (inR(c, 0x9b, 0x9f)) keep = inR(s, 0xa6, 0xa9) || inR(s, 0x9b, 0x9f);
  else if (inR(c, 0xa0, 0xa5)) keep = inR(s, 0xa0, 0xa5);
  else keep = inR(c, 0xa6, 0xa9) && inR(s, 0xa6, 0xa9);
  return keep ? previous : previous % 2 + 1;
}
