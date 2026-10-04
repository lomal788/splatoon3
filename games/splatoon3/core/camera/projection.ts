// Confirmed CPU logical projection: player_camera §6.7, r10_module_projection §6.
// General Lby renderer consumes Projection+0c (r10_render_projection §3),
// not the device/posture matrix. No physical-display X policy is inferred here.
import { F, add, sub, mul, div } from "./native_math.ts";

export interface LogicalProjectionInput {
  near: number;
  far: number;
  /** Vertical whole-angle in radians, Pose+24. */
  fovRadians: number;
  aspect: number;
  offsetX?: number;
  offsetY?: number;
  /** Supply captured original SDK tanf for bit comparisons; omitted uses the web math adapter. */
  tanHalfFov?: number;
}

/** JS libm bridge only; this function is not claimed to reproduce SDK tanf for every f32 input. */
export function webTanHalfFov(fovRadians: number): number {
  return F(Math.tan(mul(fovRadians, .5)));
}

/** 3589d74 row-major matrix. Do not cancel near or regroup depth products. */
export function logicalProjection(out: Float32Array, input: LogicalProjectionInput): Float32Array {
  const n = F(input.near), f = F(input.far), twiceNear = add(n, n);
  const h = mul(twiceNear, input.tanHalfFov ?? webTanHalfFov(input.fovRadians));
  const w = mul(h, input.aspect), midX = mul(w, input.offsetX ?? 0), midY = mul(h, input.offsetY ?? 0);
  const halfW = mul(w, .5), halfH = mul(h, .5);
  const l = sub(midX, halfW), r = add(halfW, midX), b = sub(midY, halfH), t = add(halfH, midY);
  const iw = div(1, sub(r, l)), ih = div(1, sub(t, b)), id = div(1, sub(f, n));
  out.fill(0);
  out[0] = mul(twiceNear, iw);
  out[2] = mul(add(r, l), iw);
  out[5] = mul(ih, twiceNear);
  out[6] = mul(add(t, b), ih);
  out[10] = mul(F(-add(n, f)), id);
  out[11] = mul(id, mul(mul(f, -2), n));
  out[14] = -1;
  return out;
}

export interface ProjectionViewport { left: number; top: number; right: number; bottom: number }
export interface ProjectionDrawContext { width: number; height: number; type: number }
type PoseProjection = Omit<LogicalProjectionInput, "aspect">;

/** Original matrix-before-aspect ordering and one-way M140 viewport-valid latch.
 * The client calls this per displayed frame: that cadence is a web adapter,
 * not the original CameraModule/fixed-step scheduling implementation.
 */
export class CameraProjectionState {
  readonly logical = new Float32Array(16);
  /** Original CameraModule ctor default, not a fixed screen shape. */
  aspect = F(4 / 3);
  matrixAspect = this.aspect;
  viewportValid = false;
  logicalDirty = true;
  private pose: number[] | undefined;

  update(input: PoseProjection, viewport: ProjectionViewport | null = null,
    context: ProjectionDrawContext | null = null): void {
    const pose = [input.near, input.far, input.fovRadians, input.offsetX ?? 0, input.offsetY ?? 0,
      input.tanHalfFov ?? webTanHalfFov(input.fovRadians)].map(F);
    if (!this.pose || pose.some((v, i) => v !== this.pose![i])) this.logicalDirty = true;
    this.pose = pose;
    if (this.logicalDirty) {
      this.matrixAspect = this.aspect;
      logicalProjection(this.logical, { near: pose[0], far: pose[1], fovRadians: pose[2],
        offsetX: pose[3], offsetY: pose[4], tanHalfFov: pose[5], aspect: this.matrixAspect });
      this.logicalDirty = false;
    }
    // 1010150: neither branch rewrites the already generated logical matrix.
    if (viewport) {
      this.aspect = div(sub(viewport.right, viewport.left), sub(viewport.bottom, viewport.top));
      this.viewportValid = true;
      this.logicalDirty = true;
    }
    if (context) {
      const width = Math.max(context.width & 0xffff, 1), height = context.height & 0xffff;
      this.aspect = div(width, (context.type & 0xffff) === 3 ? height : Math.max(height, 1));
      this.logicalDirty = true;
    }
  }
}

/** Web degree-valued CameraShared bridge to the original f32 radian Pose field. */
export function projectionFovRadians(degrees: number): number {
  return mul(degrees, .017453292);
}
