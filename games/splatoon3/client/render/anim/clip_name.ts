// ASB leaf clip-name resolver 0x710244d0b0 (anim_state_machine.md §3.1).
/** 0x710244d0b0 fallback chain; every candidate is rebuilt from the original name (string replace 0x710351c964 replaces all occurrences). */
const CLIP_CHAIN: [string, string][] = [["BBll", "Slsh"], ["Glng", "Spnr"], ["Brush", "Brsh"], ["Twins", "Mnvr"], ["Umbrella", "Shlt"], ["Nrml", "Shtr"]];
export interface ClipVariation { detail: string; category: string; emote: string }
/** Original candidate lookup order (anim_state_machine.md §3.1). Every candidate is cut to 63 chars. */
export function nativeClipCandidates(name: string, keys: readonly string[], v: ClipVariation): string[] {
  const out: string[] = [];
  const add = (n: string): void => { out.push(n.slice(0, 0x3f)); };
  if (keys.includes("WeaponVariation")) for (const x of [v.detail, v.category]) add(name.replaceAll("Nrml", x));
  if (keys.includes("EmoteVariation")) for (const x of [v.emote, "Win01"]) add(name.replaceAll("@", x));
  for (const [a, b] of CLIP_CHAIN) add(name.replaceAll(a, b));
  return out;
}
/** First bound candidate, or the original name when every lookup fails (the leaf then gets no entry). */
export function nativeClipName(name: string, keys: readonly string[], v: ClipVariation, exists: (clip: string) => boolean): { clip: string; found: boolean; tried: string[] } {
  const tried: string[] = [];
  for (const c of nativeClipCandidates(name, keys, v)) {
    tried.push(c);
    if (exists(c)) return { clip: c, found: true, tried };
  }
  return { clip: name.slice(0, 0x3f), found: false, tried };
}
/** Leaf key list source (ASB node → resolver param) is [미확정]; both variation keys are assumed present. */
export const ASSUMED_CLIP_KEYS = ["WeaponVariation", "EmoteVariation"] as const;
