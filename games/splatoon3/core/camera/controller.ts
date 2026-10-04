// Contract for an explicitly supplied ordinary (gyro-off) right-stick frame.
// Mouse px uses its own adapter. Scene/gyro suppliers are not invented here.
import type { NativeAxisInput, NativeYawInput } from "./stick.ts";

export interface CameraStickFrame {
  axis: Omit<NativeAxisInput, "gyro">;
  sensitivity: number;
  gyroSensitivity: number;
  controllerMode: number;
  pitchLimitBlend: number;
  yaw: Pick<NativeYawInput, "slowBlendDisabled" | "movementBlend" | "postureState" | "capDeg" | "capBlend" | "tilt">;
}
