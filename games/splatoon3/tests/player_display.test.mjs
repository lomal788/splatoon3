import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createPlayerDisplayState, stepPlayerDisplay, nativeDisplayNormalMatch,
  nativeSmDisplay, nativeHolderDisplay, nativeCornerZeroWitness, nativeCornerProbe } from '../core/player/display.ts';

const fixture=JSON.parse(readFileSync(new URL('./fixtures/player_display_r8.json',import.meta.url),'utf8'));
const fromBits=x=>new Float32Array(new Uint32Array([x]).buffer)[0];
const bits=x=>new Uint32Array(new Float32Array([x]).buffer)[0];
const flags=x=>({body:!!x[0],hlf:!!x[1],squid:!!x[2],rail:!!x[3]});
const input=i=>({ ...i, normal:i.normalBits.map(fromBits),rawNormal:i.rawNormalBits.map(fromBits),
  chargeMax:fromBits(i.chargeMaxBits),supportNormalY:fromBits(i.supportNormalYBits),verticalVelocity:fromBits(i.verticalVelocityBits),
  edgeBlend:fromBits(i.edgeBlendBits),edgeTarget:fromBits(i.edgeTargetBits) });
const resets=r=>r.flatMap(name=>[0,1,2].map(team=>[{body:0,hlf:1,commonHuman:2,squid:3}[name],team,0]));

test('Native producer handles actual 45/18/5, reversed/zero charge range, charge flags, NaN edge and i32 boundaries',()=>{
  for(const [n,c] of fixture.producer.entries()){
    const i=input(c.input),old={...c.old},got=stepPlayerDisplay(old,i);
    assert.equal(got.supported,true,`producer ${n}: ${got.reason}`);
    assert.equal(got.candidate,c.expected.candidate,`candidate ${n}`);
    assert.equal(nativeDisplayNormalMatch(i.normal,i.rawNormal),c.expected.match,`match ${n}`);
    assert.deepEqual(old,c.expected.state,`latches ${n}`);
  }
});

test('Native whole SM flags, counter threshold/model type, reset cache NaN and setter zero stay distinct',()=>{
  for(const [n,c] of fixture.sm.entries()){
    const got=nativeSmDisplay({...c.input,old:flags(c.input.old)});
    assert.deepEqual(got.flags,flags(c.flags),`SM ${n}`);
    assert.equal(got.formCounter,c.counter,`SM counter ${n}`);
    assert.deepEqual(resets(got.reset),c.resetCalls,`reset order ${n}`);
    for(const v of c.resetCaches){assert.equal(v.bits,0x7fc00000);assert.equal(v.setterBits,0);}
  }
});

test('Native whole holder timer/life guards and human/squid display priority match fixture',()=>{
  for(const [n,c] of fixture.holder.entries())
    assert.deepEqual(nativeHolderDisplay(flags(c.flags),{...c.input,old:flags(c.input.old)}),flags(c.expected),`holder ${n}`);
});

test('Native corner zero witness is conditional on probe-derived support, threshold and prior latch',()=>{
  for(const c of fixture.cornerZero){
    assert.equal(c.expectedBlendBits,0);assert.equal(c.expectedTargetBits,0);
    assert.deepEqual(nativeCornerZeroWitness(fromBits(c.afterBits),fromBits(c.loBits),fromBits(c.priorBits),fromBits(c.increaseBits)),{edgeBlend:0,edgeTarget:0});
  }
  assert.equal(nativeCornerZeroWitness(.4,.3,0,.05),undefined);
  assert.equal(nativeCornerZeroWitness(0,.3,-1,.05),undefined);
  assert.equal(nativeCornerZeroWitness(NaN,.3,0,.05),undefined);
});

test('Native corner probe start/end geometry and sphere radius match 384/10 blocks without substituting point ray',()=>{
  for(const [n,c] of fixture.cornerProbe.entries()){
    const got=nativeCornerProbe({contact:c.contactBits.map(fromBits),bodyPosition:c.bodyBits.map(fromBits),platformVelocity:c.platformBits.map(fromBits),worldTolerance:.01});
    assert.deepEqual(got.start.map(bits),c.startBits,`probe start ${n}`);assert.deepEqual(got.end.map(bits),c.endBits,`probe end ${n}`);
  }
  for(const c of fixture.cornerRadius){
    const got=nativeCornerProbe({contact:[0,0,0],bodyPosition:[0,0,0],platformVelocity:[0,0,0],worldTolerance:c.toleranceBits===null?undefined:fromBits(c.toleranceBits)});
    assert.equal(bits(got.radius),c.expectedBits);
  }
  assert.equal(nativeCornerProbe({contact:[0,0,0],bodyPosition:[Infinity,0,0],platformVelocity:[0,0,0]}),undefined);
});

test('Native producer -> whole SM -> whole holder repeats floor/wall/charge/air/exit with 288 linked frames',()=>{
  for(const t of fixture.traces){
    const state=createPlayerDisplayState();let previous=flags([0,0,1,0]);
    for(const c of t.frames){
      assert.deepEqual(state,c.old,`trace old ${t.chargeMax}/${c.frame}`);
      const bound=stepPlayerDisplay(state,input(c.input));assert.equal(bound.supported,true);
      assert.deepEqual(state,c.expected.state,`trace latches ${t.chargeMax}/${c.frame}`);
      const sm=nativeSmDisplay({hidden:bound.hidden,humanCommand:false,squidCommand:true,formCounter:0,modelKind:0,dead:false,state:c.input.state,old:previous});
      assert.deepEqual(sm.flags,flags(c.sm));assert.equal(sm.formCounter,c.counter);assert.deepEqual(resets(sm.reset),c.resetCalls);
      const holder=nativeHolderDisplay(sm.flags,{state:c.input.state,previousState:0x85,cur:0,old:previous,de0:0,df0:0,e04:0,e0c:0,e1c:0,d60:0,d5c:0,life30:false,life31:false,life35:true,life38:0,debug:false,special:0,selected:false,specialDisabled:false});
      assert.deepEqual(holder,flags(c.holder));previous=sm.flags;
    }
  }
});

test('Missing producers are explicit unsupported and preserve latches; irrelevant edges do not block visible stable state',()=>{
  const i=input(fixture.producer[0].input);Object.assign(i,{state:0x85,airFrames:0,paintClass:0,dokanKind:0,grindActive:false,ceilingTimer:0,chargeFrames:0,b781:false,b7f4:false,b7f9:false,railLatch:false,forceByte:false,launchActive:false,wallChargeRelease:false,normal:[0,1,0],rawNormal:[0,1,0],edgeBlend:undefined,edgeTarget:undefined});
  const state=createPlayerDisplayState(),before={...state};assert.equal(stepPlayerDisplay(state,i).supported,false);assert.deepEqual(state,before);
  const stable=stepPlayerDisplay(state,{...i,paintClass:2});assert.equal(stable.supported,true);assert.equal(stable.hidden,false);
  assert.equal(stepPlayerDisplay(state,{...i,warpActive:true}).supported,false);
  assert.equal(stepPlayerDisplay(state,{...i,chargeMax:NaN}).supported,false);
  assert.equal(stepPlayerDisplay(state,{...i,airFrames:1,verticalVelocity:.1,supportNormalY:undefined}).supported,false);
  // Coordinate mismatch makes f=1 independently of unknown corner producers.
  assert.equal(stepPlayerDisplay(state,{...i,rawNormal:[0,.5,0]}).supported,true);
});
