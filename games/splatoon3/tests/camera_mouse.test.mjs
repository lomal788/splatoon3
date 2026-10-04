import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import { PerspectiveCamera, Quaternion, Vector3 } from "three";
import { PlayerCamera } from "../core/camera/camera.ts";
import { emptyPad, Btn } from "../core/input.ts";
import { defaultCameraSettings, InputDevice, mouseToLook } from "../client/input.ts";
import { createCameraView } from "../client/camera/index.ts";
import { floatBits } from "../core/camera/native_math.ts";
const deg=180/Math.PI;
const near=(a,b,e=1e-4)=>assert.ok(Math.abs(a-b)<=e,`${a} vs ${b}`);
const angle=(a,b)=>Math.atan2(a[2]*b[0]-a[0]*b[2],a[0]*b[0]+a[2]*b[2])*deg;
const angle3=(a,b)=>Math.atan2(Math.hypot(...new Vector3().fromArray(a).cross(new Vector3().fromArray(b)).toArray()),a.reduce((n,v,i)=>n+v*b[i],0))*deg;
function build(extra={}) {
  const c=new PlayerCamera(),pl={pos:[0,0,0],forward:[0,0,1],floorNormal:[0,1,0],...extra};
  c.reset(pl,false);for(let i=0;i<120;i++)c.step(pl,emptyPad(),null);
  const camera=new PerspectiveCamera(),view=createCameraView({camera}),w={shared:new Map([["camera",c.out]])};
  const render=a=>{view.update(w,a);return camera.getWorldDirection(new Vector3()).toArray();};
  const step=(dx=0,dy=0,s=defaultCameraSettings())=>{const p=emptyPad();p.lookMode="mouse";[p.lookYaw,p.lookPitch]=mouseToLook(dx,dy,s);c.step(pl,p,null);return p;};
  return {c,pl,camera,view,w,render,step};
}
function event(target,type,props={}) {const e=new Event(type,{cancelable:true});for(const [k,v]of Object.entries(props))Object.defineProperty(e,k,{value:v});target.dispatchEvent(e);}
function env(locked=true) {
  const names=["document","addEventListener","removeEventListener","localStorage"],old=names.map(k=>Object.getOwnPropertyDescriptor(globalThis,k));
  const win=new EventTarget(),doc=new EventTarget(),el=new EventTarget();doc.pointerLockElement=locked?el:null;doc.visibilityState="visible";
  el.requestPointerLock=()=>Promise.resolve();
  globalThis.document=doc;globalThis.addEventListener=win.addEventListener.bind(win);globalThis.removeEventListener=win.removeEventListener.bind(win);
  globalThis.localStorage={getItem:()=>null,setItem:()=>{}};
  const input=new InputDevice(el);
  return {win,doc,el,input,move:(dx,dy=0)=>event(win,"mousemove",{movementX:dx,movementY:dy}),
    key:(code,type="keydown")=>event(win,type,{code}),lock:value=>{doc.pointerLockElement=value?el:null;event(doc,"pointerlockchange");},
    dispose(){input.dispose();names.forEach((k,i)=>old[i]?Object.defineProperty(globalThis,k,old[i]):delete globalThis[k]);}};
}

test("mouse preserves signed yaw and complete turns above 180 degrees",()=>{
  for(const turn of [-210,-270,-450,-720,210,270,450,720]) {
    const h=build();h.step(-turn/.15);let prev=h.render(0),sum=0;
    for(let i=1;i<=64;i++){const now=h.render(i/64),d=angle(prev,now);assert.ok(d*Math.sign(turn)>0);sum+=d;prev=now;}
    near(sum,turn,.002);
    assert.ok(new Vector3().fromArray(h.c.out.viewForward).distanceTo(new Vector3().fromArray(prev))<1e-6);
  }
});
test("mouse yaw orbit preserves distance and alpha endpoints instead of crossing player",()=>{
  const h=build(),start=h.camera.position.clone();h.render(0);start.copy(h.camera.position);
  const dist=new Vector3().fromArray(h.c.out.pos).distanceTo(new Vector3().fromArray(h.c.out.target));h.step(1400);
  for(const a of [0,.25,.5,.75,1]){h.render(a);const target=new Vector3().fromArray(h.c.out.prevTarget).lerp(new Vector3().fromArray(h.c.out.target),a);near(h.camera.position.distanceTo(target),dist,.001);}
  h.render(0);assert.ok(h.camera.position.distanceTo(start)<1e-6);
  h.render(1);assert.ok(h.camera.position.distanceTo(new Vector3().fromArray(h.c.out.pos))<1e-6);
});
test("mouse pitch stops at native curve target with zero-input follow travel",()=>{
  for(const dy of [-2000,-600,-200,200,600,2000]) {
    const h=build();h.step(0,dy);const first=h.render(1),p=h.c.out.pitchNorm;
    for(let i=0;i<60;i++){h.step();near(h.c.out.pitchNorm,p,1e-7);near(angle3(first,h.render(1)),0,.001);}
  }
});
test("unmarked pad preserves native pitch-follow behavior",()=>{
  const h=build();const p=emptyPad();[,p.lookPitch]=mouseToLook(0,-200,defaultCameraSettings());h.c.step(h.pl,p,null);
  const first=h.render(1),pn=h.c.out.pitchNorm;h.c.step(h.pl,emptyPad(),null);
  assert.ok(h.c.out.pitchNorm>pn);assert.ok(angle3(first,h.render(1))>1);
});
test("mouse inversion, scalar wrap and diagonal residual basis retain requested direction",()=>{
  for(const invertX of [false,true]) {
    const h=build(),before=h.render(1);h.step(1400,-200,{...defaultCameraSettings(),invertX});
    const quarter=h.render(.25);assert.equal(Math.sign(angle(before,quarter)),invertX?1:-1);
    h.render(1);assert.ok(new Vector3().fromArray(h.c.out.viewForward).distanceTo(h.camera.getWorldDirection(new Vector3()))<1e-6);
    assert.ok(Number.isFinite(h.camera.quaternion.length()));
  }
  const h=build();let previous=h.render(1),sum=0;for(let i=0;i<240;i++){h.step(10);const next=h.render(1),d=angle(previous,next);assert.ok(d<0);sum+=d;previous=next;}near(sum,-360,.005);
});
test("reset, FOV and floor-normal changes preserve basis endpoints and world shake",()=>{
  const h=build();h.step(1400,-100);h.pl.floorNormal=[.6,.8,0];h.pl.pos=[2,1,3];h.pl.squid=true;h.step(-1400,200);
  h.render(0);assert.ok(h.camera.position.distanceTo(new Vector3().fromArray(h.c.out.prevPos))<1e-6);
  h.render(1);assert.ok(new Vector3().fromArray(h.c.out.viewForward).distanceTo(h.camera.getWorldDirection(new Vector3()))<1e-6);
  near(h.camera.fov,h.c.out.fov,1e-8);const q=h.camera.quaternion.clone(),pos=h.camera.position.clone();
  h.camera.userData.shakeOffset={x:.1,y:.2,z:-.3};h.render(1);assert.ok(q.angleTo(h.camera.quaternion)<1e-7);assert.ok(h.camera.position.distanceTo(pos.add(new Vector3(.1,.2,-.3)))<1e-8);
  h.c.reset(h.pl,true,[1,0,0]);assert.equal(h.c.out.mouseYawDelta,0);assert.equal(h.c.out.mouseLook,false);
  h.render(.5);assert.ok(h.camera.position.distanceTo(new Vector3().fromArray(h.c.out.pos).add(new Vector3(.1,.2,-.3)))<1e-6);
});
test("catch-up partitions all pending displacement without magnitude clamping",()=>{
  const e=env();try {e.move(1400,-200);const pads=[5,4,3,2,1].map(n=>e.input.sample(n));
    // px policy is unchanged; native pitchMax(0)=bits3FE66666 replaces double1.8.
    near(pads.reduce((s,p)=>s+p.lookYaw,0)*deg,-210,1e-10);near(pads.reduce((s,p)=>s+p.lookPitch,0)*deg,200*.15*floatBits(0x3fe66666)/4,1e-10);
    for(const p of pads){near(p.lookYaw*deg,-42,1e-10);assert.equal(p.lookMode,"mouse");}
    near(e.input.sample().lookYaw,0,1e-12);
    const h=build(),start=h.render(1);for(const p of pads)h.c.step(h.pl,p,null);
    const pre=h.render(0),post=h.render(1);near(angle(pre,post),-42,.002);near(angle(start,pre),-168,.002);
  }finally{e.dispose();}
});
test("actual app frame callback distributes catch-up and preserves substep pending input",()=>{
  const e=env();try{
    const text=readFileSync(new URL("../client/app.ts",import.meta.url),"utf8"),start=text.indexOf("  const frame = (now: number): void => {"),end=text.indexOf("\n  requestAnimationFrame(frame);",start);
    assert.ok(start>0&&end>start);const frameJS=stripTypeScriptTypes(text.slice(start,end),{mode:"strip"}),pads=[],h=build();
    const hosts={input:e.input,world:{step:p=>{pads.push({...p});h.c.step(h.pl,p,null);}},views:[{update:(w,a)=>h.render(a)}],click:{style:{}},audio:{state:"running"},ctx:{},renderer:{render(){}},scene:{},camera:{},debug:null,debugText:()=>"",requestAnimationFrame(){}};
    const frame=Function(...Object.keys(hosts),`const STEP=1/60,MAX_STEPS=5;let acc=0,last=0;${frameJS};return frame;`)(...Object.values(hosts));
    e.move(1400);frame(8);assert.equal(pads.length,0);frame(1000);
    assert.equal(pads.length,5);near(pads.reduce((s,p)=>s+p.lookYaw,0)*deg,-210,1e-10);for(const p of pads)near(p.lookYaw*deg,-42,1e-10);
    near(h.c.out.mouseYawDelta*deg,-42,.001);
  }finally{e.dispose();}
});
test("lock loss clears pending delta and held actions with one release edge",()=>{
  const e=env();try{e.key("KeyW");event(e.el,"mousedown",{button:0});assert.equal(e.input.sample().hold,Btn.Fire);
    e.move(1400,-200);e.lock(false);e.key("KeyR");const p=e.input.sample();near(p.lookYaw,0,1e-12);near(p.lookPitch,0,1e-12);assert.equal(p.hold,0);assert.equal(p.moveY,0);assert.equal(p.trigger,0);assert.equal(p.release,Btn.Fire);assert.equal(e.input.sample().release,0);
    e.lock(true);e.move(10);near(e.input.sample().lookYaw*deg,-1.5,1e-10);
  }finally{e.dispose();}
});
test("blur and hidden tab discard pending mouse input and recover on focus",()=>{
  const e=env();try{e.move(1400);event(e.win,"blur");e.move(1400);near(e.input.sample().lookYaw,0,1e-12);
    event(e.win,"focus");e.move(10);near(e.input.sample().lookYaw*deg,-1.5,1e-10);
    e.move(1400);e.doc.visibilityState="hidden";event(e.doc,"visibilitychange");e.move(1400);near(e.input.sample().lookYaw,0,1e-12);
    e.doc.visibilityState="visible";event(e.doc,"visibilitychange");e.move(10);near(e.input.sample().lookYaw*deg,-1.5,1e-10);
  }finally{e.dispose();}
});
test("nonfinite axes cannot poison queued valid input; settings boundaries stay consistent",()=>{
  const e=env();try{e.move(10,20);e.move(Infinity,NaN);const p=e.input.sample();near(p.lookYaw*deg,-1.5,1e-10);near(p.lookPitch*deg,-20*.15*floatBits(0x3fe66666)/4,1e-10);
    e.input.setSettings({...defaultCameraSettings(),sens:Infinity,mouseScale:NaN});assert.equal(e.input.settings.sens,0);assert.equal(e.input.settings.mouseScale,1);
    e.input.setSettings({...defaultCameraSettings(),sens:99,mouseScale:99});assert.equal(e.input.settings.sens,5);assert.equal(e.input.settings.mouseScale,20);
  }finally{e.dispose();}
});
test("dispose removes new input lifetime listeners",()=>{
  const e=env();try{e.move(1400);e.key("KeyR");e.input.dispose();e.key("KeyR");e.move(1400);assert.equal(e.input.sample().hold,0);near(e.input.sample().lookYaw,0,1e-12);}finally{e.dispose();}
});
