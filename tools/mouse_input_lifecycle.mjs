import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { stripTypeScriptTypes } from 'node:module';
import { InputDevice, defaultCameraSettings, loadCameraSettings, mouseToLook } from '../games/splatoon3/client/input.ts';
import { Btn } from '../games/splatoon3/core/input.ts';

const output = resolve('analysis/mouse_camera/input/lifecycle_execution.json');
const hashes = {};
for (const p of ['web/games/splatoon3/client/input.ts','web/games/splatoon3/client/app.ts','web/games/splatoon3/core/input.ts','web/games/splatoon3/core/camera/index.ts','web/games/splatoon3/core/player/index.ts']) hashes[p] = createHash('sha256').update(readFileSync(p)).digest('hex');

const rows = [];
function check(name, actual, expected, note = '') {
  const pass = typeof expected === 'function' ? expected(actual) : JSON.stringify(actual) === JSON.stringify(expected);
  rows.push({ name, pass, actual, expected: typeof expected === 'function' ? expected.toString() : expected, note });
  if (!pass) throw Error(`Failed: ${name} ${JSON.stringify(actual)}`);
}
function event(target, type, props = {}) {
  const e = new Event(type, {cancelable:true});
  for(const [k,v] of Object.entries(props)) Object.defineProperty(e,k,{value:v});
  target.dispatchEvent(e);
  return e;
}
function env(locked = true, storage = {}) {
  const win = new EventTarget();
  const doc = new EventTarget();
  const el = new EventTarget();
  const calls = [];
  el.requestPointerLock = (...args) => { calls.push(args); return Promise.resolve(); };
  doc.pointerLockElement = locked ? el : null;
  globalThis.document = doc;
  globalThis.addEventListener = win.addEventListener.bind(win);
  globalThis.removeEventListener = win.removeEventListener.bind(win);
  const values = new Map(Object.entries(storage));
  globalThis.localStorage = {getItem:k=>values.has(k)?values.get(k):null,setItem:(k,v)=>values.set(k,v)};
  const input = new InputDevice(el);
  const move = (dx,dy=0) => event(win,'mousemove',{movementX:dx,movementY:dy});
  const key = (code,type='keydown') => event(win,type,{code});
  const lock = value => {doc.pointerLockElement = value ? el : null; event(doc,'pointerlockchange');};
  const dispose = () => input.dispose();
  return {win,doc,el,calls,input,move,key,lock,values,dispose};
}
const deg = rad => rad*180/Math.PI;
const near = (a,b,e=1e-10)=>Math.abs(a-b)<e;

{
  const e=env(); e.move(30,10); e.move(-10,-4);
  const a=e.input.sample(), b=e.input.sample();
  check('normal_events_accumulate_once', [deg(a.lookYaw),deg(a.lookPitch)], x=>near(x[0],-3)&&near(x[1],-.405));
  check('second_sample_has_zero_delta', [b.lookYaw,b.lookPitch], [0,0]); e.dispose();
}
{
 const e=env(false); e.move(1200,1200);
 check('unlocked_move_ignored', [e.input.sample().lookYaw,e.input.sample().lookPitch], [0,0]);
 event(e.el,'mousedown',{button:0});
 check('unlock_click_requests_no_options',e.calls,[[]]); e.lock(true);
 check('unlock_click_not_fire',e.input.sample().hold&Btn.Fire,0); e.dispose();
}
{
 const e=env(); e.move(1200,100); e.key('KeyW'); event(e.el,'mousedown',{button:0}); const before=e.input.sample();
 e.move(1200,100); e.lock(false); event(e.doc,'visibilitychange');
 const after=e.input.sample();
 check('lockloss_keeps_pending_delta',deg(after.lookYaw), x=>near(x,-180));
 check('lockloss_keeps_key_and_button', [after.moveY,after.hold&Btn.Fire,after.trigger&Btn.Fire],[1,1,0]);
 e.lock(true); check('relock_does_not_retrigger_held_fire', e.input.sample().trigger&Btn.Fire,0); e.dispose();
}
{
 const e=env(); e.key('KeyW'); e.key('KeyR'); event(e.el,'mousedown',{button:0}); e.input.sample();
 e.move(1200,100); event(e.win,'blur'); e.lock(false);
 const after=e.input.sample();
 check('blur_keeps_pending_delta',deg(after.lookYaw),x=>near(x,-180));
 check('blur_clears_keys_buttons', [after.moveY,after.hold], [0,0]);
 check('blur_prev_hold_release_retained',after.release,Btn.Reset|Btn.Fire); e.dispose();
}
{
 const e=env(false); e.key('KeyR'); const a=e.input.sample();
 check('unlocked_keyR_triggers_reset', a.trigger,Btn.Reset);
 e.key('KeyR'); check('repeat_keydown_not_extra_reset',e.input.sample().trigger,0);
 e.key('KeyR','keyup'); check('keyR_release_edge',e.input.sample().release,Btn.Reset); e.dispose();
}
{
 const e=env(); e.move(1200); const a=e.input.sample();
 check('single_1200px_returns_180deg',deg(a.lookYaw),x=>near(x,-180));
 e.input.setSettings({...defaultCameraSettings(),mouseScale:20}); e.move(60);
 check('scale20_60px_returns_180deg',deg(e.input.sample().lookYaw),x=>near(x,-180));
 e.input.setSettings({...defaultCameraSettings(),sens:5,mouseScale:20}); e.move(240/7);
 check('sens5_scale20_34point285px_returns_180deg',deg(e.input.sample().lookYaw),x=>near(x,-180)); e.dispose();
}
{
 const e=env(); e.move(10); e.input.setSettings({...defaultCameraSettings(),mouseScale:20});
 check('queued_delta_uses_sample_time_settings',deg(e.input.sample().lookYaw),x=>near(x,-30));
 e.move(Infinity); const inf=e.input.sample();
 check('nonfinite_delta_not_filtered',String(inf.lookYaw),'-Infinity');
 e.move(NaN); e.move(1); const nan=e.input.sample();
 check('NaN_event_poison_until_sample',Number.isNaN(nan.lookYaw),true);
 check('sample_clears_poisoned_accumulator',e.input.sample().lookYaw,0); e.dispose();
}
{
 const e=env(true,{'splatoon3.camera.sens':'20','splatoon3.camera.mouseScale':'99'});
 check('load_settings_clamps_to_sens5_scale20',[e.input.settings.sens,e.input.settings.mouseScale],[5,20]); e.dispose();
}

// Execute the actual saved app.ts frame callback, with render/audio/world hosts captured as fixtures.
const appSource=readFileSync('web/games/splatoon3/client/app.ts','utf8');
const start=appSource.indexOf('  const frame = (now: number): void => {');
const end=appSource.indexOf('\n  requestAnimationFrame(frame);',start);
if(start<0||end<0) throw Error('Actual frame extraction boundary changed');
const frameTS=appSource.slice(start,end);
const frameJS=stripTypeScriptTypes(frameTS,{mode:'strip'});
function actualFrame(input) {
 const pads=[], renders=[], queue=[];
 const hosts = {input,world:{step:p=>pads.push({...p})},views:[{update:(w,a)=>renders.push(a)}],click:{style:{}},audio:{state:'running',resume:()=>Promise.resolve()},ctx:{},renderer:{render(){}},scene:{},camera:{},debug:null,debugText:()=>'',requestAnimationFrame:f=>queue.push(f)};
 const names=Object.keys(hosts), values=Object.values(hosts);
 const create=Function(...names,`const STEP=1/60; const MAX_STEPS=5; let acc=0,last=0; ${frameJS}; return {frame,getAcc:()=>acc,getLast:()=>last};`);
 return {...create(...values),pads,renders,queue,hosts};
}
{
 const e=env(); const loop=actualFrame(e.input); e.move(1200); loop.frame(8);
 check('substep_frame_does_not_consume_delta',loop.pads.length,0);
 loop.frame(1000/60);
 check('next_step_consumes_queued_delta',loop.pads.map(p=>deg(p.lookYaw)),x=>x.length===1&&near(x[0],-180)); e.dispose();
}
{
 const e=env(); const loop=actualFrame(e.input); e.move(1200); loop.frame(1000);
 check('resume_capped_to_five_steps',loop.pads.length,5);
 check('catchup_first_step_takes_all_delta',loop.pads.map(p=>deg(p.lookYaw)),x=>x.length===5&&near(x[0],-180)&&x.slice(1).every(v=>v===0));
 check('catchup_alpha_range',loop.renders[0],x=>x>=0&&x<1); e.dispose();
}
{
 const e=env();const loop=actualFrame(e.input); e.move(1200);e.lock(false);event(e.win,'blur');loop.frame(1000/60);
 check('actual_frame_steps_and_consumes_while_unlocked',loop.pads.map(p=>[deg(p.lookYaw),p.hold]),x=>x.length===1&&near(x[0][0],-180)&&x[0][1]===0);e.dispose();
}
{
 const e=env(false);const loop=actualFrame(e.input);e.key('KeyR');loop.frame(1000/60);
 check('actual_frame_passes_unlocked_reset_to_world',loop.pads.map(p=>p.trigger),[Btn.Reset]);e.dispose();
}
{
 const e=env(); e.input.dispose();e.move(1200);e.key('KeyR');
 check('dispose_removes_event_listeners',e.input.sample().trigger|e.input.sample().lookYaw,0);
}
const result={date:'2026-10-03',level:'웹실행',original_binary_executed:false,source_hashes:hashes,source_files_changed:false,fixture_boundaries:['DOM event delivery is synthetic, no browser mouse device or OS acceleration','actual InputDevice/mouseToLook/loadCameraSettings module is imported','actual app.ts frame callback is extracted and TypeScript erased, host world/render/audio fixtures','no GPU or original game execution','1200px/Infinity/NaN are injected stress values, not observed user input'],test_count:rows.length,pass:rows.filter(r=>r.pass).length,fail:rows.filter(r=>!r.pass).length,rows};
mkdirSync(dirname(output),{recursive:true});writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({output,test_count:result.test_count,pass:result.pass,fail:result.fail,original_binary_executed:false}));
