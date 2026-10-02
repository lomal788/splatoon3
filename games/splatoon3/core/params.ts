// GameParameterTable 조회: 필드 단위 $parent 상속 → 코드 생성자 기본값 (docs/02_code_and_params.md §2, 01 §3).
// 데이터는 클라이언트가 읽어 넘긴다(assets/data/params/*.json, assets/data/param_defaults.json).
export type ParamObject = Record<string, unknown> & { $type?: string };

export interface ParamTable {
  $parent?: string;
  GameParameters?: Record<string, ParamObject>;
}

export class ParamStore {
  readonly tables: Record<string, ParamTable>;
  readonly defaults: Record<string, Record<string, unknown>>;

  constructor(tables: Record<string, ParamTable>, defaults: Record<string, Record<string, unknown>>) {
    this.tables = tables;
    this.defaults = defaults;
  }

  /** 표 이름(예: "WeaponShooterNormal")의 키(예: "MoveParam")를 기본값까지 병합해 돌려준다. */
  get<T = Record<string, unknown>>(table: string, key: string): T {
    const chain: ParamObject[] = [];
    let type: string | undefined;
    for (let name: string | undefined = table, guard = 0; name && guard < 16; guard++) {
      const t: ParamTable | undefined = this.tables[name];
      if (!t) break;
      const obj = t.GameParameters?.[key];
      if (obj) {
        chain.push(obj);
        type ??= obj.$type;
      }
      name = parentName(t.$parent);
    }
    const out: Record<string, unknown> = { ...(type ? this.defaults[type] : undefined) };
    for (let i = chain.length - 1; i >= 0; i--) for (const [k, v] of Object.entries(chain[i])) if (k !== "$type") out[k] = v;
    if (type) out.$type = type;
    return out as T;
  }

  has(table: string): boolean {
    return table in this.tables;
  }
}

/** "Work/Component/GameParameterTable/X.game__GameParameterTable.gyml" → "X" */
export function parentName(ref?: string): string | undefined {
  if (!ref) return undefined;
  const base = ref.slice(ref.lastIndexOf("/") + 1);
  return base.slice(0, base.indexOf("."));
}
