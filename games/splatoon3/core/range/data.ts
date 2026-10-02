// 사격장 상수·기본값. 근거: docs/range/shooting_range.md (주소·확정 수준은 그 문서 §4).
// 에셋 번들(maps/<map>/params/*.json, common/data/param_defaults.json)에 값이 있으면 그것을 쓰고,
// 없을 때만 아래 값(원본 데이터·생성자 판독값)을 쓴다.
import { f32 } from "../fmath.ts";

/** spl__SighterTargetParam 생성자 기본값 (팩토리 0x71020cb944, 방문 0x71020cba38) [판독] */
export const SIGHTER_PARAM_DEFAULTS = {
  Scale: 1.0,
  BurstWaitDispFrame: 120,
  NoDamageRefreshFrame: 120,
  LossOfColorWaitFrame: 60,
  BulletImpulsScaler: f32(0.06),
  BombImpulsScaler: 1.0,
  PlayerImpulsScaler: f32(0.03),
  DamageInfoOffsetY: f32(2.6),
  DrawDamageInfoDistance: 40.0,
  IsAlwaysDrawDamageInfo: false,
  IsTipsTrial: false,
};

export type SighterParam = typeof SIGHTER_PARAM_DEFAULTS;

/** spl__BendCalculatorParam 생성자 기본값 (방문 0x7101dd4858) [판독] */
export const BEND_PARAM_DEFAULTS = { Kp: 0.0, Kd: 0.0 };

/**
 * 액터 팩 GameParameterTable 원본 값 [데이터] (Pack/Actor/SighterTarget*.pack.zs).
 * 표 이름 = 파일 이름. SighterTarget_Large·_TipsTrial 은 $parent = SighterTarget.
 */
export const SIGHTER_TABLES: Record<string, { parent?: string; sighter: Partial<SighterParam>; bend?: { Kp: number; Kd: number }; maxHitPoint?: number }> = {
  SighterTarget: {
    sighter: { BombImpulsScaler: f32(0.1), BulletImpulsScaler: f32(1.66), PlayerImpulsScaler: f32(0.005), Scale: 1.0 },
    bend: { Kp: f32(0.05), Kd: f32(0.9) },
    maxHitPoint: 1000,
  },
  SighterTarget_Large: { parent: "SighterTarget", sighter: { Scale: f32(1.3) }, maxHitPoint: 5000 },
  SighterTarget_TipsTrial: { parent: "SighterTarget", sighter: { IsTipsTrial: true } },
};

/** 배치 이름 → GameParameterTable 이름, 모델(fmdb) 이름 [데이터: ActorParam Components] */
export const SIGHTER_ACTORS: Record<string, { table: string; model: string; elink: string }> = {
  SighterTarget: { table: "SighterTarget", model: "Obj_SighterTarget", elink: "SighterTarget" },
  SighterTarget_Large: { table: "SighterTarget_Large", model: "Obj_SighterTarget", elink: "SighterTargetBig" },
  SighterTarget_Move: { table: "SighterTarget", model: "Obj_SighterTargetMove", elink: "SighterTarget" },
  SighterTarget_TipsTrial: { table: "SighterTarget_TipsTrial", model: "Obj_SighterTarget", elink: "SighterTarget_TipsTrial" },
  SighterTarget_TipsTrialMove: { table: "SighterTarget_TipsTrial", model: "Obj_SighterTargetMove", elink: "SighterTarget_TipsTrial" },
};

/**
 * 충돌 캡슐(액터 로컬, 스케일 1) [데이터: Phive/ShapeParam/SighterTarget*.phive__ShapeParam].
 * ColBullet = 탄이 맞는 몸(마스크 SplPlayerSensor ⊃ SplInkBullet), Main = 플레이어·물체를 막는 몸(마스크 SplPlayerColOthers).
 */
export const SIGHTER_SHAPES = {
  colBullet: { a: [0, f32(1.3), 0], b: [0, f32(0.35), 0], radius: f32(0.35) },
  main: { a: [0, f32(1.26), f32(0.35)], b: [0, f32(0.39), 0], radius: f32(0.39) },
} as const;

/** Obj_SighterTarget.bfres 스켈레탈 애니 프레임 수 [데이터]. Wait 는 애니 이름이 "" (0x71021f10d8). */
export const SIGHTER_ANIM_FRAMES: Record<string, number> = {
  "": 0,
  DamageShot: 30,
  Brust: 1, // 원본 철자 그대로 ("Brust")
  Expand: 45,
  Flick: 24,
  DamageShotBend: 360, // 반복, 프레임 = 휨 방향(도)
};

/** 접촉 종류별 휨 충격 계수표 0x7104a9d010 [데이터]: 0 탄, 1 플레이어, 2 폭탄 */
export const BEND_KIND_SCALE = [f32(0.005), f32(0.01), f32(0.015)];

/** LocatorInfo(RSDB) ShapeType·Scale [데이터] */
export const AREA_LOCATORS: Record<string, { shape: "Cube" | "Cylinder"; scale: number }> = {
  LobbyShootingArea: { shape: "Cube", scale: 1.0 },
  LobbyShootingArea_Cylinder: { shape: "Cylinder", scale: 1.0 },
};

/** 플레이어 공중 프레임 임계(상수표 0x71058bbb78+0xa8 = 0x71058bbc20 = 4) [판독+실행(정적 초기화 에뮬)] */
export const AIR_FRAMES_LATCH = 4;
