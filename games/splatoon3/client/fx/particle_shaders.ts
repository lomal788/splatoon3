export const VERT = /* glsl */ `
#include <common>
attribute float aSlot;
attribute vec4 fxVertexColor;
attribute vec4 tangent;
attribute vec2 uv1;
attribute float vatRow;
uniform highp sampler2D uParticles;
vec4 state(int col) { return texelFetch(uParticles,ivec2(col,int(aSlot)),0); }
uniform float uNow;
uniform float uAir;
uniform float uRotRegist;
uniform vec4 uScaleK[8];
uniform int uScaleN;
uniform vec4 uAlphaK[8];
uniform int uAlphaN;
uniform int uAlphaType;
uniform vec4 uColorK[8];
uniform int uColorN;
uniform int uColorType;
uniform vec3 uPivot;
uniform int uPlane;     // 0 = 그대로(XY), 1 = POLYGON_XZ(Rx −90°: 로컬 Y → −Z) [추정], 2 = 구 근사(y 크기 = x)
uniform int uBill;      // 0 카메라 빌보드, 2 Y 빌보드, 5 VelLook(카메라 빌보드로 근사), 3/4 폴리곤(이미터 축)
uniform int uRotOrder;  // 4 YZX, 6 ZXY, 그 밖 XYZ
uniform float uLoopRate;
uniform float uLoopRandom;
varying vec2 vUv;
varying vec4 vColor;
varying vec4 vColor1;
varying vec4 vPrimitive;
varying vec3 vWorld;
varying vec3 vNormal;
varying vec4 vTangent;
varying vec2 vUv1;
uniform vec4 uColor1K[8],uAlpha1K[8];
uniform int uColor1N,uAlpha1N,uColor1Type,uAlpha1Type;
uniform vec4 uPeriods;
uniform vec4 uPhases;
uniform vec4 uKeyModes;
uniform float uScaleMode;
uniform sampler2D uVat;
uniform int uHasVat;
uniform float uVatRate,uVatNormalOffset;
float channelTime(float age,float life,float r,float period,float phase) {
  return period>0.?fract((r*phase*period+age)/period):age/life;
}
// Native A is compact normal, not opacity. WebGL packHalf2x16 preserves the finite half sample.
vec3 vatNormal(float a) {
  uint h=packHalf2x16(vec2(a,0.))&65535u;
  int j=(h<32768u?int(h)-1024:33792-int(h))+30719;
  float phi=float(j)*3.88322115;
  float z=float(j)*2.*(-1.6276572e-5)+.999983728;
  float x=abs(z);
  float aa=(((x*(-.0187293)+.0742610022)*x-.2121144)*x+1.5707288)*sqrt(1.-x);
  float theta=z<0.?3.1415927-2.*aa+aa:aa;
  return vec3(sin(theta)*cos(phi),z,sin(theta)*sin(phi));
}

vec4 keyLerp(vec4 k[8], int cnt, float t, float mode) {
  if (cnt <= 1) return k[0];
  if (t < k[0].w) return k[0];
  for (int i = 1; i < 8; i++) {
    if (i >= cnt) break;
    if (t < k[i].w) {
      float d = k[i].w - k[i - 1].w;
      float s = d > 0.0 ? (t - k[i - 1].w) / d : 1.0;
      return mode==1.?k[i-1]:mix(k[i - 1], k[i], s);
    }
  }
  for (int i = 7; i >= 0; i--) { if (i < cnt) return k[i]; }
  return k[0];
}

mat3 rx(float a) { float c = cos(a), s = sin(a); return mat3(1.0, 0.0, 0.0, 0.0, c, s, 0.0, -s, c); }
mat3 ry(float a) { float c = cos(a), s = sin(a); return mat3(c, 0.0, -s, 0.0, 1.0, 0.0, s, 0.0, c); }
mat3 rz(float a) { float c = cos(a), s = sin(a); return mat3(c, s, 0.0, -s, c, 0.0, 0.0, 0.0, 1.0); }

void main() {
  vec3 aOrigin=state(0).xyz,aBx=state(1).xyz,aBy=state(2).xyz,aBz=state(3).xyz;
  vec3 aP0=state(4).xyz,aV0=state(5).xyz,aG=state(6).xyz;
  vec4 aTime=state(7),aRand=state(11);
  vec3 aScale0=state(8).xyz,aRot0=state(9).xyz,aRotAdd=state(10).xyz,aColor=state(12).xyz;
  vColor1=vec4(0.);vPrimitive=fxVertexColor;vUv1=uv1;
  vWorld=vec3(0.);vNormal=vec3(0.,1.,0.);vTangent=vec4(1.,0.,0.,1.);
  float t = uNow - aTime.x;
  vUv = uv;
  if (aTime.w < 0.5 || t < 0.0 || t >= aTime.y) {
    gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
    vColor = vec4(0.0);
    return;
  }
  float a = uAir;
  float f = a == 1.0 ? t : (1.0 - pow(a, t)) / (1.0 - a);
  float g = a == 1.0 ? 0.5 * t * t : (t - (pow(a, t) - 1.0) / log(a)) / (1.0 - a);
  vec3 P = aP0 + aTime.z * (aV0 * f + aG * g);
  float tn = uLoopRate > 0.0 ? fract((aRand.x * uLoopRandom * uLoopRate + t) / uLoopRate) : t / aTime.y;
  vec3 sc = keyLerp(uScaleK, uScaleN, tn,uScaleMode).xyz * aScale0;
  if (uPlane == 2) sc.y = sc.x;
  float r = uRotRegist;
  float R = r == 1.0 ? t : (1.0 - pow(r, t)) / (1.0 - r);
  vec3 rot = aRot0 + aRotAdd * R;
  mat3 M = uRotOrder == 4 ? ry(rot.y) * rz(rot.z) * rx(rot.x)
         : uRotOrder == 6 ? rz(rot.z) * rx(rot.x) * ry(rot.y)
         : rx(rot.x) * ry(rot.y) * rz(rot.z);
  vec3 q = position,nLocal=normal;
  if(uHasVat==1){
    int width=textureSize(uVat,0).x;
    float qt=clamp(min(t*uVatRate/(float(width)+.00001)+.00001,.99999),0.,1.);
    float vf=float(width)*fract(qt);int x0=int(vf),x1=x0<width-1?x0+1:x0;
    // vatRow is original sysTexCoordAttr.z, never a synthesized vertex index.
    int row=int(vatRow);
    vec4 p0=texelFetch(uVat,ivec2(x0,row),0),p1=texelFetch(uVat,ivec2(x1,row),0);
    q=mix(p0.xyz,p1.xyz,fract(vf));
    nLocal=mix(vatNormal(p0.w),vatNormal(p1.w),fract(vf));
    if(any(notEqual(q,vec3(0.))))nLocal+=q*uVatNormalOffset;
  }
  vec3 v = uPlane == 1 ? vec3(q.x, q.z, -q.y) : q;
  v = (v + 0.5 * uPivot) * sc;
  vec3 lv = M * v;
  vec3 center = aOrigin + aBx * P.x + aBy * P.y + aBz * P.z;
  mat3 basis=mat3(aBx,aBy,aBz);
  if(uBill==0||uBill==5)basis=transpose(mat3(viewMatrix));
  else if(uBill==2){vec3 fz=normalize(vec3(cameraPosition.x-center.x,0.,cameraPosition.z-center.z));basis=mat3(normalize(cross(vec3(0.,1.,0.),fz)),vec3(0.,1.,0.),fz);}
  vWorld=center+basis*lv;
  vNormal=basis*M*nLocal;
  vTangent=vec4(basis*M*tangent.xyz,tangent.w);
  if (uBill == 0 || uBill == 5) {
    vec4 vc = viewMatrix * vec4(center, 1.0);
    gl_Position = projectionMatrix * (vc + vec4(lv, 0.0));
  } else if (uBill == 2) {
    vec3 tc = cameraPosition - center;
    tc.y = 0.0;
    float tl = length(tc);
    vec3 fz = tl > 1e-5 ? tc / tl : vec3(0.0, 0.0, 1.0);
    vec3 rx = normalize(cross(vec3(0.0, 1.0, 0.0), fz));
    gl_Position = projectionMatrix * viewMatrix * vec4(center + rx * lv.x + vec3(0.0, 1.0, 0.0) * lv.y + fz * lv.z, 1.0);
  } else {
    vec3 world = center + aBx * lv.x + aBy * lv.y + aBz * lv.z;
    gl_Position = projectionMatrix * viewMatrix * vec4(world, 1.0);
  }
  vec4 ct=vec4(channelTime(t,aTime.y,aRand.x,uPeriods.x,uPhases.x),channelTime(t,aTime.y,aRand.x,uPeriods.y,uPhases.y),channelTime(t,aTime.y,aRand.x,uPeriods.z,uPhases.z),channelTime(t,aTime.y,aRand.x,uPeriods.w,uPhases.w));
  float al=uAlphaType==2?keyLerp(uAlphaK,uAlphaN,ct.y,uKeyModes.y).x:uAlphaK[0].x;
  float a1=uAlpha1Type==2?keyLerp(uAlpha1K,uAlpha1N,ct.w,uKeyModes.w).x:uAlpha1K[0].x;
  vec3 c0=uColorType==2?keyLerp(uColorK,uColorN,ct.x,uKeyModes.x).xyz:uColorK[0].xyz;
  vec3 c1=uColor1Type==2?keyLerp(uColor1K,uColor1N,ct.z,uKeyModes.z).xyz:uColor1K[0].xyz;
  // Existing team input is a named web bridge for native dynamic[0/1]; producer remains unknown.
  vColor=vec4(aColor*c0,al);vColor1=vec4(aColor*c1,a1);

}
`;

export const FRAG = /* glsl */ `
uniform sampler2D uMap,uMap1,uMap2;
uniform int uProgram,uHasNormal,uLightingAvailable;
uniform float uHasMap,uColorScale,uAlphaThreshold,uLinkedAlpha,uFade,uSoftDistance;
uniform vec2 uAlphaRemap,uNearFade;
uniform float uWebRoughness,uWebFresnel;
uniform sampler2D uSceneDepth;
uniform float uDepthNear,uDepthFar;
uniform vec2 uDepthResolution;
uniform int uDepthAvailable;
uniform vec3 hLightColor,hLightDirection;
uniform vec4 hSH[7],hDepthFog,hHeightFog;
uniform vec3 hDepthRange,hGridOrigin,hInvCell;
uniform vec2 hHeightRange;
uniform highp usampler2D hGrid;
uniform vec4 hDynColor[30],hDynAtt[30],hDynPos[30],hDynDir[30];
varying vec2 vUv,vUv1;
varying vec4 vColor,vColor1,vPrimitive,vTangent;
varying vec3 vWorld,vNormal;
vec3 fxSH(vec3 n){
  vec4 v=vec4(n,1.),q=vec4(n.x*n.y,n.y*n.z,n.z*n.z,n.x*n.z);
  return max(vec3(0.),vec3(dot(hSH[0],v),dot(hSH[1],v),dot(hSH[2],v))+vec3(dot(hSH[3],q),dot(hSH[4],q),dot(hSH[5],q))+(n.x*n.x-n.y*n.y)*hSH[6].rgb);
}
vec3 fxSpec(vec3 n,vec3 v,vec3 l){
  vec3 h=normalize(v+l);float nh=max(dot(n,h),1.e-8),nl=max(dot(n,l),1.e-8),nv=max(dot(n,v),1.e-8),vh=max(dot(v,h),1.e-8);
  float r=uWebRoughness,r2=r*r,r4=r2*r2,k=(r*.5+.5)*(r*.5+.5)*.5;
  float d=max(nh*nh*(r4-1.)+1.,1.e-8),a=(r2/d)*(r2/d)/((k+(1.-k)*nl)*(k+(1.-k)*nv));
  float f=exp2(vh*(vh*-5.55473-6.98316002));return vec3(uWebFresnel+(1.-uWebFresnel)*f)*a*.0795774683;
}
vec3 fxDynamic(vec3 n,vec3 v,vec3 base){
  ivec2 cell=clamp(ivec2((vWorld.xz-hGridOrigin.xz)*hInvCell.xz),ivec2(0),ivec2(19));
  uint packed=texelFetch(hGrid,cell,0).r;vec3 c=vec3(0.);
  for(int k=0;k<4;k++){
    uint i=(packed>>uint(k*8))&255u;if(i>=30u)break;
    vec3 delta=hDynPos[i].xyz-vWorld;float d=length(delta);vec3 l=delta/max(d,1.e-8);vec4 at=hDynAtt[i];
    float a=pow(clamp(1.-at.x*d,0.,1.),at.y)*clamp(dot(n,l),0.,1.);
    if(hDynPos[i].w!=0.)a*=pow(clamp((-dot(l,hDynDir[i].xyz)-at.z)/(1.-at.z),0.,1.),at.w);
    c+=hDynColor[i].rgb*a*(base*.318309873+fxSpec(n,v,l));
  }return c;
}
float linearDepth(float d){return uDepthNear*uDepthFar/(uDepthFar-d*(uDepthFar-uDepthNear));}
void main(){
  vec4 t0=vec4(1.),t1=vec4(1.),t2=vec4(1.);
  if(uHasMap>.5)t0=texture2D(uMap,vUv);
  else {vec2 d=vUv*2.-1.;t0.a=clamp(1.-dot(d,d),0.,1.);}
  if(uHasNormal==1)t1=texture2D(uMap1,vUv);
  if(uProgram==1202)t2=texture2D(uMap2,vUv);
  float nearFade=uNearFade.y>uNearFade.x?clamp((length(cameraPosition-vWorld)-uNearFade.x)/(uNearFade.y-uNearFade.x),0.,1.):1.;
  float fade=nearFade*uFade,soft=1.;
  if(uProgram==1897&&uDepthAvailable==1&&uSoftDistance>0.){
    float scene=texture2D(uSceneDepth,gl_FragCoord.xy/uDepthResolution).r;
    soft=clamp((linearDepth(scene)-linearDepth(gl_FragCoord.z))/uSoftDistance,0.,1.);
  }
  vec3 c0=vColor.rgb*uColorScale,c1=vColor1.rgb*uColorScale;
  float rawA;vec3 base;
  if(uProgram==1383||uProgram==1385){rawA=clamp(vColor.a*uLinkedAlpha,0.,1.)*fade;base=c0;}
  else if(uProgram==1202){rawA=clamp(t1.a*t2.a*uLinkedAlpha*vColor.a,0.,1.)*fade;base=c0;}
  else if(uProgram==1747){rawA=clamp(t0.a*uLinkedAlpha*vColor.a,0.,1.)*fade;base=t0.rgb*c0+c1;}
  else if(uProgram==1897||uProgram==1885){rawA=soft*clamp((t0.a*vPrimitive.a-vColor.a)*vColor1.a,0.,1.)*fade;base=c0*vPrimitive.rgb;}
  else if(uProgram==1886){rawA=clamp((t0.a*vPrimitive.a-vColor.a)*vColor1.a,0.,1.)*fade;base=(t0.rgb*c0+c1)*vPrimitive.rgb;}
  else if(uProgram==1940){rawA=clamp(t0.a*vPrimitive.a*vColor.a,0.,1.)*uFade;base=(t0.rgb*c0+c1)*vPrimitive.rgb;}
  else {rawA=clamp(t0.r*vColor.a,0.,1.);base=c0;} // Prior web fallback; no native claim for unknown programs.
  if(rawA<=uAlphaThreshold)discard;
  float mappedA=rawA*uAlphaRemap.x+uAlphaRemap.y;
  vec3 n=normalize(vNormal);
  if(uHasNormal==1){
    vec3 tangent=vTangent.xyz-n*dot(n,vTangent.xyz);
    if(dot(tangent,tangent)<1.e-8){vec3 dp1=dFdx(vWorld),dp2=dFdy(vWorld);vec2 uvA=dFdx(vUv),uvB=dFdy(vUv);tangent=dp1*uvB.y-dp2*uvA.y;}
    tangent=normalize(tangent);vec3 binormal=cross(n,tangent)*vTangent.w;
    vec2 xy=t1.xy*2.-1.;n=normalize(tangent*xy.x+binormal*xy.y+n*sqrt(max(0.,1.-dot(xy,xy))));
  }
  vec3 rgb=base;
  // Native Custom1 BRDF/lighting coefficients and env-layer6 remain unresolved.
  // This consumes the stage's actual light/SH/dynamic/fog via an explicitly documented web bridge.
  if(uLightingAvailable==1){
    vec3 v=normalize(cameraPosition-vWorld),l=normalize(-hLightDirection);
    float nl=max(dot(n,l),0.);
    rgb=base*fxSH(n)+hLightColor*nl*(base*.318309873+fxSpec(n,v,l))+fxDynamic(n,v,base);
    float z=linearDepth(gl_FragCoord.z);
    float fd=clamp((z-hDepthRange.x)/max(hDepthRange.y-hDepthRange.x,1.e-8),0.,1.);
    float fh=clamp((hHeightRange.y-vWorld.y)/max(hHeightRange.y-hHeightRange.x,1.e-8),0.,1.);
    rgb=mix(rgb,hDepthFog.rgb,fd*hDepthFog.a);rgb=mix(rgb,hHeightFog.rgb,fh*hHeightFog.a);
  }
  if(uProgram==1885&&mappedA<=0.)rgb=vec3(1.,0.,0.);
  gl_FragColor=vec4(rgb,clamp(mappedA,0.,1.));
  #include <colorspace_fragment>
}
`;
