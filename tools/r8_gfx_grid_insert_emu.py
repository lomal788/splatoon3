"""Original DynamicLight bounds/grid setting and point insertion. No algorithm stubs; original SDK cosf."""
import json,random,struct,sys,math
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from network_uc import UC,BASE
from r5_player_libm_emu import Sdk
ROOT=Path(__file__).resolve().parents[2];F=np.float32
add=lambda a,b:F(F(a)+F(b));sub=lambda a,b:F(F(a)-F(b));mul=lambda a,b:F(F(a)*F(b));div=lambda a,b:F(F(a)/F(b))
fb=lambda x:F(struct.unpack('<f',struct.pack('<I',x))[0])
e=UC();sdk=Sdk();a=e.alloc(0x1100);size=e.alloc(0x10);center=e.alloc(0x10);pos=e.alloc(0x10);dr=e.alloc(0x10);co=e.alloc(0x10)
def vec(p,v):e.mu.mem_write(p,struct.pack('<%df'%len(v),*v))
def hook(mu,pc,sz,_):
 if pc==BASE+0x3e9be30:mu.reg_write(UC_ARM64_REG_S0,sdk.call('cosf',fb(mu.reg_read(UC_ARM64_REG_S0)&0xffffffff)));mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
e.mu.hook_add(UC_HOOK_CODE,hook)
rg=random.Random(10457);checks=0
for k in range(2048):
 s=[F(rg.uniform(-40,40)) for _ in range(3)]
 if k<9:s[k//3]=[F(0),F(2**-23),F(-2**-23)][k%3]
 cen=[F(rg.uniform(-100,100)) for _ in range(3)];vec(size,s);vec(center,cen);e.call(BASE+0x1044f90,a,size,center)
 q=[F(1) if abs(x)<=F(2**-23) else x for x in s];extent=[mul(q[0],20),q[1],mul(q[2],20)];ori=[sub(cen[i],mul(extent[i],.5)) for i in range(3)]
 assert bytes(e.mu.mem_read(a+0xff8,12))==struct.pack('<3f',*q)
 assert bytes(e.mu.mem_read(a+0x1004,12))==struct.pack('<3f',*extent)
 assert bytes(e.mu.mem_read(a+0x1010,12))==struct.pack('<3f',*ori)
for k in range(1024):
 cell=[F(10),F(1),F(10)];cen=[F(0),F(0),F(0)];vec(size,cell);vec(center,cen);e.call(BASE+0x1044f90,a,size,center);ori=[F(-100),F(-.5),F(-100)]
 e.mu.mem_write(a+0x2b0,b'\xff'*0x640);e.u32(a+0x101c,0);grid=[0xffffffff]*400;n=0
 for j in range(8):
  p=[F(rg.uniform(-170,170)),F(rg.uniform(-30,30)),F(rg.uniform(-170,170))];radius=F(rg.uniform(.1,60));d=[F(rg.uniform(-2,2)) for _ in range(3)];col=[F(rg.uniform(0,4)) for _ in range(4)];damp=F(rg.uniform(.1,5))
  if k%8==0:p=[F(0),F(j),F(0)];radius=F(3)
  vec(pos,p);vec(dr,d);vec(co,col);ret=e.call(BASE+0x104560c,a,pos,dr,co,0,fargs=(radius,0,damp,0))
  local=[sub(p[0],ori[0]),mul(cell[1],.5),sub(p[2],ori[2])];cx=math.floor(float(div(local[0],cell[0])));cz=math.floor(float(div(local[2],cell[2])));rx=math.ceil(float(div(radius,cell[0])));rz=math.ceil(float(div(radius,cell[2])));accepted=False
  for x in range(cx-rx,cx+rx+1):
   for z in range(cz-rz,cz+rz+1):
    if not(0<=x<20 and 0<=z<20):continue
    dx=sub(mul(add(x,.5),cell[0]),local[0]);dz=sub(mul(add(z,.5),cell[2]),local[2]);dist=F(np.sqrt(add(mul(dx,dx),mul(dz,dz))))
    if dist<add(mul(max(cell[0],cell[2]),F(.70710677)),radius):
     t=z*20+x
     if grid[t]>>24==255:grid[t]=((grid[t]<<8)|n)&0xffffffff;accepted=True
  assert bool(ret&1)==accepted,(k,j,'ret')
  if accepted:
   assert bytes(e.mu.mem_read(a+0x8f0+n*16,16))==struct.pack('<4f',*col)
   assert bytes(e.mu.mem_read(a+0xad0+n*16,16))==struct.pack('<4f',div(1,radius),damp,1,0)
   assert bytes(e.mu.mem_read(a+0xcb0+n*12,12))==struct.pack('<3f',*p)
   ln=F(np.sqrt(add(add(mul(d[0],d[0]),mul(d[1],d[1])),mul(d[2],d[2]))));q=[mul(v,div(1,ln)) for v in d] if ln>0 else d
   assert bytes(e.mu.mem_read(a+0xe18+n*12,12))==struct.pack('<3f',*q)
   assert struct.unpack('<I',e.mu.mem_read(a+0xf80+n*4,4))[0]==0;n+=1
  assert bytes(e.mu.mem_read(a+0x2b0,1600))==struct.pack('<400I',*grid),(k,j,'grid');assert struct.unpack('<I',e.mu.mem_read(a+0x101c,4))[0]==n;checks+=1
out={'grid_setting_2048':True,'point_insertion_inputs':checks,'packed400_cells_bit_match':True,'color_atten_position_direction_flags_bit_match':True,'stubs':[],'SDK':'original cosf executes separately','limits':'Spot cone grid has 판독 only; whole scene/NVN not executed'}
(ROOT/'analysis/completion/r8/grid_insert_emu.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))
