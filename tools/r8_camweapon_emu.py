"""r8 original camera-input copies and rumble calculations; synthetic inputs only.
No game state, hardware, resource loading or actuators execute. See boundary hooks in result.
"""
import json,random,struct,sys
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC,STUB
ROOT=Path(__file__).resolve().parents[2];F=np.float32
B=0x7100000000

def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
def add(a,b):return F(F(a)+F(b))
def sub(a,b):return F(F(a)-F(b))
def mul(a,b):return F(F(a)*F(b))
def div(a,b):return F(F(a)/F(b))
class Run:
 def __init__(self):
  self.u=UC();self.mu=self.u.mu;self.mode='';self.created=0
  self.m=self.u.alloc(0x500);self.p=self.u.alloc(0x200);self.res=self.u.alloc(0x200);self.hand=self.u.alloc(0x80);self.h=self.u.alloc(0x80);self.voice=self.u.alloc(0x100);self.vt=self.u.alloc(0x100);self.a=self.u.alloc(0x30);self.z=self.u.alloc(0x30);self.inp=self.u.alloc(0x4058);self.src=self.u.alloc(0x4058)
  self.ptr(B+0x582a710,self.m);self.ptr(B+0x59a57d0,self.p);self.ptr(self.p,self.vt);self.ptr(self.res+0x158,self.p);self.ptr(self.hand+0x28,self.res)
  self.ptr(self.vt,STUB+0x300);self.ptr(self.vt+0x38,STUB+0x308)
  self.mu.mem_write(B+0x582a570,b'\1');self.mu.mem_write(B+0x582a4a8,b'\1')
  self.ptr(self.voice,self.vt);self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def ptr(self,a,v):self.mu.mem_write(a,struct.pack('<Q',v))
 def ret(self,v=None):
  if v is not None:self.mu.reg_write(UC_ARM64_REG_X0,v)
  self.mu.reg_write(UC_ARM64_REG_PC,self.mu.reg_read(UC_ARM64_REG_LR))
 def hook(self,mu,pc,n,_):
  if pc==B+0x130dc14:self.ret(self.hand)
  elif pc==B+0x38a15e8:self.ret()
  elif pc==STUB+0x300:self.ret(1)
  elif pc==STUB+0x308:self.ret(0)
  elif self.mode=='gyro' and pc==B+0x3d55638:self.ret(self.p)
  elif self.mode=='gyro' and pc==B+0x26c01d0:self.ret()
  elif self.mode=='limiter' and pc in [B+0x3e99fd0,B+0x3e99ff0]:self.ret()
  elif self.mode=='limiter' and pc==B+0x130fe58:
   self.created+=1;h=mu.reg_read(UC_ARM64_REG_X0);self.ptr(h+0x40,self.voice);self.u.u32(h+0x48,7);self.ret()
 def distance(self,A,Z,lo,hi,factor):
  self.mode='distance';self.mu.mem_write(self.a,struct.pack('<3f',*A));self.mu.mem_write(self.z,struct.pack('<3f',*Z))
  for off,v in [(0x68,lo),(0x64,hi),(0x60,factor)]:self.u.f32(self.p+off,v)
  self.mu.mem_write(self.p+0x6e,b'\1\1\1');self.u.call(B+0x130d764,self.a,self.z)
  got=self.mu.reg_read(UC_ARM64_REG_S0)&0xffffffff
  d=F(np.sqrt(add(add(mul(sub(A[0],Z[0]),sub(A[0],Z[0])),mul(sub(A[1],Z[1]),sub(A[1],Z[1]))),mul(sub(A[2],Z[2]),sub(A[2],Z[2])))))
  def ramp(x,a,b):return F(0) if x<=a else F(1) if x>=b else div(sub(x,a),sub(b,a)) if b!=a else F(0)
  r=ramp(d,F(lo),F(hi)) if lo<=hi else sub(1,ramp(d,F(hi),F(lo)))
  return got,bits(mul(r,factor))
 def copy(self,vals,coef,category,valid):
  self.mode='copy';self.mu.mem_write(self.h,b'\0'*0x80);self.ptr(self.h+0x40,self.voice);self.u.u32(self.h+0x48,7 if valid else 8);self.u.u32(self.voice+0x10,7);self.u.u32(self.h+0x10,category)
  for off,v in zip([0x24,0x28,0x2c,0x34,0x38],vals):self.u.f32(self.h+off,v)
  for i,c in enumerate(coef):self.u.f32(self.m+0x108+i*8,c)
  self.u.u32(self.voice+0x64,0x12345678);self.u.u32(self.voice+0x6c,0x23456789)
  self.u.call(B+0x130fffc,self.h)
  got=[self.u.ru32(self.voice+x) for x in [0x64,0x6c]]
  ref=[bits(max(mul(mul(mul(vals[0],vals[1]),vals[2]),coef[category if category<3 else 0]),F(0))),bits(max(mul(vals[3],vals[4]),F(.01)))] if valid else [0x12345678,0x23456789]
  return got,ref
 def gyro(self,raw,vel):
  self.mode='gyro';self.mu.mem_write(B+0x58bbb8b,b'\0\0');self.mu.mem_write(self.inp+0x5ac,struct.pack('<9f',*raw));self.mu.mem_write(self.inp+0x5a0,struct.pack('<3f',*vel));self.u.call(B+0x26bf9f8,self.inp)
  got=list(struct.unpack('<12I',self.mu.mem_read(self.inp+0x3f50,48)))
  ref=[bits(f) for f in raw]+[bits(mul(v,struct.unpack('<f',struct.pack('<I',0x3d6e4baf))[0])) for v in vel]
  return got,ref
 def options(self,vals):
  self.mode='options';self.mu.mem_write(self.src+0x70,struct.pack('<iiBBB',*vals));self.u.call(B+0x2a0b044,self.inp+0x3f88,self.src)
  return bytes(self.mu.mem_read(self.inp+0x3ff8,11)).hex(),struct.pack('<iiBBB',*vals).hex()
 def poser(self,raw):
  self.mode='poser';self.u.u32(self.inp+0x16a8,0xffffffff);self.mu.mem_write(self.inp+0x88,raw);self.mu.mem_write(self.src+0x298,b'\0'*0xb0);self.ptr(self.src+0x290,self.src);self.u.call(B+0x24e50c0,self.inp);pose=self.mu.reg_read(UC_ARM64_REG_X0);self.u.call(B+0x1017d5c,self.src+0x298,pose);self.mu.mem_write(self.m,b'\xa5'*0x4c);self.u.call(B+0x27600c8,self.src+0x288,self.m)
  got=bytes(self.mu.mem_read(self.m,0x4c));ref=bytearray(b'\xa5'*0x4c)
  for a,z in [(0,0x2d),(0x30,0x45),(0x48,0x4c)]:ref[a:z]=raw[a:z]
  return got.hex(),bytes(ref).hex()
 def limiter(self,counter,match,limit):
  self.mode='limiter';self.mu.mem_write(self.m,b'\0'*0x500);e=self.m+0x200;t=self.m+0x280;n=self.m+0x350
  self.ptr(e+8,t);self.u.u32(e+0x10,2);self.ptr(t,self.p);self.u.u32(t+0xc,2);self.mu.mem_write(self.p+0x3c,b'\1\1');self.ptr(self.p+0x30,n);self.mu.mem_write(n,b'GMBT_ToSquidMix00.bnvib\0');self.u.u32(self.p+0x38,limit);self.u.u32(e,counter)
  self.ptr(self.m+0x168,e);self.u.u32(self.m+0x174,1);self.u.u32(self.m+0x160,1);self.ptr(self.m+0x150,self.h);self.ptr(self.h,self.m+0x150);self.ptr(self.h+8,self.m+0x150);self.ptr(self.m+0x138,self.m+0x138);self.ptr(self.m+0x140,self.m+0x138)
  self.ptr(self.a,n if match else self.z);self.mu.mem_write(self.z,b'Other.bnvib\0');self.created=0;self.u.call(B+0x130f0b8,self.m,1,self.a,0,fargs=(0,))
  got=[self.created,self.u.ru32(e)];ref=[0,counter&0xffffffff] if match and counter>0 else [1,(limit if match else counter)&0xffffffff]
  return got,ref
 def tick(self,c):
  self.mode='tick';self.ptr(self.m+0x168,self.m+0x200);self.u.u32(self.m+0x174,1);self.u.u32(self.m+0x200,c);self.mu.reg_write(UC_ARM64_REG_X19,self.m);self.mu.reg_write(UC_ARM64_REG_W9,0);self.mu.emu_start(B+0x130ef5c,B+0x130efbc,count=1000)
  return self.u.ru32(self.m+0x200),(c-1 if c>0 else c)&0xffffffff

def main():
 r=Run();rng=random.Random(882031);out={'boundaries':['distance resource/RTTI resolution and ref cleanup stubbed; direct parameter flags only','voice active vt38 returns false; no actuator/hardware','gyro input-core sampling/filtering stubbed; preloaded filtered buffers; debug flags0','limiter mutex and waveform allocation stubbed; original manager admission/counter/reset code executes','poser getter default C16a8=-1; interpolation disabled; original getter/interpolator/consumer execute; frame selection/device posture not executed'], 'cases':{}}
 def test(name,cases):
  n=0
  for c in cases:
   got,ref=c
   if got!=ref:raise AssertionError((name,n,got,ref))
   n+=1
  out['cases'][name]={'pass':n,'mismatch':0}
 test('distance',[r.distance([rng.uniform(-40,40) for _ in range(3)],[rng.uniform(-10,10) for _ in range(3)],lo,hi,fac) for lo,hi in [(30,4),(4,30),(4,4),(0,0),(-1,2),(80,10)] for fac in [0,.3,1,2] for _ in range(48)])
 test('gain_pitch',[r.copy([rng.uniform(-2,3) for _ in range(5)],[.5,1,2],cat,valid) for cat in [0,1,2,3,100,0xffffffff] for valid in [True,False] for _ in range(96)])
 test('gyro_output',[r.gyro([rng.uniform(-1,1) for _ in range(9)],[rng.uniform(-360,360) for _ in range(3)]) for _ in range(512)])
 test('options_copy',[r.options((i,20-i,1,ud,lr)) for i in range(21) for ud in range(2) for lr in range(2)])
 test('poser_copy',[r.poser(rng.randbytes(0x4c)) for _ in range(512)])
 test('limiter_admission',[r.limiter(c,m,l) for c in [-1,0,1,8] for m in [True,False] for l in [0,1,8,12]])
 test('limiter_tick',[r.tick(c) for c in [-2147483648,-1,0,1,2,8,2147483647]])
 p=ROOT/'analysis/completion/r8/camera_emu.json';p.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
