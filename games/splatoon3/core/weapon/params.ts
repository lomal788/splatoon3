// 무기·탄 파라미터 조회. 근거: docs/weapon/shooter_bullet.md §4.1, analysis/param_reflect/*.json(생성자 기본값).
import type { ParamStore } from "../params.ts";

export interface MoveParam {
  SpawnSpeed: number;
  GoStraightToBrakeStateFrame: number;
  GoStraightStateEndMaxSpeed: number;
  BrakeGravity: number;
  BrakeAirResist: number;
  BrakeToFreeVelocityY: number;
  BrakeToFreeVelocityXZ: number;
  BrakeToFreeStateFrame: number;
  FreeGravity: number;
  FreeAirResist: number;
}

export interface CollisionParam {
  InitRadiusForPlayer: number;
  EndRadiusForPlayer: number;
  ChangeFrameForPlayer: number;
  FriendThroughFrameForPlayer: number;
  InitRadiusForField: number;
  EndRadiusForField: number;
  ChangeFrameForField: number;
}

export interface DamageParam {
  ValueMax: number;
  ValueMin: number;
  ReduceStartFrame: number;
  ReduceEndFrame: number;
}

export interface ShooterPaintParam {
  DistanceNear: number;
  DistanceMiddle: number;
  DistanceFar: number;
  WidthHalfNear: number;
  WidthHalfMiddle: number;
  WidthHalfFar: number;
  DegreeUseDepthScaleMin: number;
  DegreeUseDepthScaleMax: number;
  DepthScaleMin: number;
  DepthScaleMax: number;
  HeightUseDepthScaleMinBreakFree: number;
  HeightUseDepthScaleMaxBreakFree: number;
  DepthScaleMinBreakFree: number;
  DepthScaleMaxBreakFree: number;
}

export interface SplashPaintParam {
  WidthHalf: number;
  WidthHalfNearest: number;
  DepthScaleMin: number;
  DepthScaleMax: number;
  DepthMinDropHeight: number;
  DepthMaxDropHeight: number;
}

export interface SplashSpawnParam {
  SpawnNum: number;
  SpawnBetweenLength: number;
  SplitNum: number;
  SpawnNearestLength: number;
  RandomSpawnVelXMax: number;
  RandomSpawnVelYMax: number;
  RandomSpawnVelZMin: number;
  RandomSpawnVelZMax: number;
  ForceSpawnNearestAddNumArray: number[];
}

export interface WeaponShooterParam {
  InkConsume: number;
  InkRecoverStop: number;
  RepeatFrame: number;
  Stand_DegSwerve: number;
  Stand_DegBiasMin: number;
  Stand_DegBiasMax: number;
  Stand_DegBiasKf: number;
  Stand_DegBiasDecrease: number;
  Jump_DegSwerve: number;
  Jump_DegBiasMax: number;
  Jump_DegBiasDecreaseStartFrame: number;
  Jump_DegBiasEndFrame: number;
  MoveSpeed: number;
  ShotGuideFrame: number;
  PreDelayFrame_HumanShot: number;
  PreDelayFrame_SquidShot: number;
  SquidShotShorteningFrame: number;
  PostDelayFrame: number;
  TripleShotSpanFrame: number;
  VariableShotRepeatStartFrame: number;
}

export interface AdditionParam {
  XRate: number;
  ZRate: number;
  YPlusRate: number;
  YMinusRate: number;
  GuideYMinusZero: boolean;
  YMax: number;
}

export interface TailLengthParam {
  DelayShotFrame: number;
  MaxLengthFrame: number;
  StartMaxLength: number;
  EndMaxLength: number;
}

export interface WallDropCollisionPaintParam {
  PaintRadiusShock: number;
  PaintRadiusFall: number;
  PaintRadiusGround: number;
  FallPeriodFirstSecondTargetAlp: number;
}

export interface WallDropMoveParam {
  FreeGravityType: string;
  FallPeriodFirstTargetSpeed: number;
  FallPeriodFirstFrameMin: number;
  FallPeriodFirstFrameMax: number;
  FallPeriodSecondTargetSpeed: number;
  FallPeriodSecondFrame: number;
  FallPeriodLastFrameMin: number;
  FallPeriodLastFrameMax: number;
}

export interface WallDropCommonParam {
  InitVelocityRateYPlus: number;
  InitVelocityRateYMinus: number;
  PaintWallSpanMinFrame: number;
  PaintWallSpanMaxFrame: number;
  PaintWallDropDistance: number;
}

export const DEFAULTS = {
  spl__BulletSimpleMoveParam: {
    SpawnSpeed: 2.0, GoStraightToBrakeStateFrame: 10, GoStraightStateEndMaxSpeed: 10.0, BrakeGravity: 0.07000000029802322,
    BrakeAirResist: 0.36000001430511475, BrakeToFreeVelocityY: -0.15000000596046448, BrakeToFreeVelocityXZ: 0.23549999296665192,
    BrakeToFreeStateFrame: 4, FreeGravity: 0.01600000075995922, FreeAirResist: 0.019999999552965164,
  } satisfies MoveParam,
  spl__BulletSimpleCollisionParam: {
    InitRadiusForPlayer: 0.20000000298023224, EndRadiusForPlayer: 0.20000000298023224, ChangeFrameForPlayer: 0,
    FriendThroughFrameForPlayer: 0, InitRadiusForField: 0.20000000298023224, EndRadiusForField: 0.20000000298023224, ChangeFrameForField: 0,
  } satisfies CollisionParam,
  spl__BulletShooterDamageParam: { ValueMax: 180, ValueMin: 120, ReduceStartFrame: 8, ReduceEndFrame: 24 } satisfies DamageParam,
  spl__BulletShooterPaintParam: {
    DistanceNear: 2.0, DistanceMiddle: 20.0, DistanceFar: 20.0, WidthHalfNear: 1.399999976158142, WidthHalfMiddle: 1.399999976158142,
    WidthHalfFar: 1.399999976158142, DegreeUseDepthScaleMin: 35.0, DegreeUseDepthScaleMax: 10.0, DepthScaleMin: 1.399999976158142,
    DepthScaleMax: 2.4000000953674316, HeightUseDepthScaleMinBreakFree: 10.0, HeightUseDepthScaleMaxBreakFree: 1.5,
    DepthScaleMinBreakFree: 1.2000000476837158, DepthScaleMaxBreakFree: 2.4000000953674316,
  } satisfies ShooterPaintParam,
  spl__BulletSplashShooterPaintParam: {
    WidthHalf: 1.2799999713897705, WidthHalfNearest: 1.7920000553131104, DepthScaleMin: 1.0, DepthScaleMax: 1.2000000476837158,
    DepthMinDropHeight: 10.0, DepthMaxDropHeight: 3.0,
  } satisfies SplashPaintParam,
  spl__BulletSplashShooterSpawnParam: {
    SpawnNum: 0.0, SpawnBetweenLength: 0.0, SplitNum: 1, SpawnNearestLength: 0.0, RandomSpawnVelXMax: 0.054999999701976776,
    RandomSpawnVelYMax: 0.014999999664723873, RandomSpawnVelZMin: 0.009999999776482582, RandomSpawnVelZMax: 0.019999999552965164,
    ForceSpawnNearestAddNumArray: [] as number[],
  } satisfies SplashSpawnParam,
  spl__WeaponShooterParam: {
    InkConsume: 0.008999999612569809, InkRecoverStop: 20, RepeatFrame: 6, Stand_DegSwerve: 0.0, Stand_DegBiasMin: 0.10000000149011612,
    Stand_DegBiasMax: 0.25, Stand_DegBiasKf: 0.019999999552965164, Stand_DegBiasDecrease: 0.009999999776482582, Jump_DegSwerve: 0.0,
    Jump_DegBiasMax: 0.0, Jump_DegBiasDecreaseStartFrame: 0, Jump_DegBiasEndFrame: 45, MoveSpeed: 0.0, ShotGuideFrame: 8,
    PreDelayFrame_HumanShot: 0, PreDelayFrame_SquidShot: 4, SquidShotShorteningFrame: 0, PostDelayFrame: 4, TripleShotSpanFrame: 0,
    VariableShotRepeatStartFrame: 0,
  } satisfies WeaponShooterParam,
  spl__SpawnBulletAdditionMovePlayerParam: {
    XRate: 0.4000000059604645, ZRate: 2.0, YPlusRate: 1.0, YMinusRate: 0.0, GuideYMinusZero: false, YMax: 100.0,
  } satisfies AdditionParam,
  spl__BulletShooterTailLengthParam: { DelayShotFrame: 3, MaxLengthFrame: 10, StartMaxLength: 20.0, EndMaxLength: 1.5 } satisfies TailLengthParam,
  spl__BulletWallDropCollisionPaintParam: {
    PaintRadiusShock: 1.2999999523162842, PaintRadiusFall: 0.6499999761581421, PaintRadiusGround: 0.6000000238418579,
    FallPeriodFirstSecondTargetAlp: 1.0,
  } satisfies WallDropCollisionPaintParam,
  spl__BulletWallDropMoveParam: {
    FreeGravityType: "00000000", FallPeriodFirstTargetSpeed: 0.05999999865889549, FallPeriodFirstFrameMin: 10, FallPeriodFirstFrameMax: 30,
    FallPeriodSecondTargetSpeed: 0.05999999865889549, FallPeriodSecondFrame: 10, FallPeriodLastFrameMin: 15, FallPeriodLastFrameMax: 20,
  } satisfies WallDropMoveParam,
  spl__BulletWallDropCommonParam: {
    InitVelocityRateYPlus: 0.014999999664723873, InitVelocityRateYMinus: 0.03500000014901161, PaintWallSpanMinFrame: 2,
    PaintWallSpanMaxFrame: 4, PaintWallDropDistance: 0.0,
  } satisfies WallDropCommonParam,
};

export type ParamTypeName = keyof typeof DEFAULTS;

/** 표 + 키 조회 → 코드 기본값으로 빈 필드를 채운다(ParamStore 의 param_defaults 가 없어도 동작). */
export function readParam<T extends object>(store: ParamStore | null | undefined, table: string, key: string, type: ParamTypeName): T {
  const base = DEFAULTS[type] as unknown as T;
  if (!store || !store.has(table)) return { ...base };
  const got = store.get<Record<string, unknown>>(table, key);
  const out: Record<string, unknown> = { ...(base as Record<string, unknown>) };
  for (const [k, v] of Object.entries(got)) if (k !== "$type" && v !== undefined) out[k] = v;
  return out as T;
}

/** 무기 id → 원본 GameParameterTable 이름(무기 액터 팩 Pack/Actor/WeaponShooterNormal, 탄 BulletSplashShooter·BulletWallDrop 표). */
export interface WeaponTables {
  main: string;
  splash: string;
  wallDrop: string;
}

export const WEAPON_TABLES: Record<string, WeaponTables> = {
  Shooter_Normal_00: { main: "WeaponShooterNormal", splash: "BulletSplashShooter", wallDrop: "BulletWallDrop" },
};
