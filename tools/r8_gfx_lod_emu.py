"""r8 original Model LOD selector + static model packet byte comparison; no hooks."""
import sys,struct,random,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC
R=Path(__file__).resolve().parents[2]
def f(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def put(b,o,v):struct.pack_into('<f',b,o,f(v))
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def ref(unit,rec,sp,base,mn,n,mode,bias,h):
 out=bytearray(unit)
 if out[0x11]&1:return out
 dest=struct.unpack_from('<Q',out,8)[0]
 if dest!=sp:
  out[0x10]=min(n-1,out[0x1f])&255;return out
 old=out[0x10]
 if mode:
  st=f(f(f(struct.unpack_from('<f',unit,0x18)[0]+struct.unpack_from('<f',rec,0)[0])+struct.unpack_from('<f',rec,0x5c)[0])+bias)
  if n<2 or not base>st:out[0x10]=mn&255;return out
  inv=struct.unpack_from('<f',rec,8)[0];q=f(f(base-st)*inv)
  if h<=0:
   if q<=1:idx=int(f(f(q*f(n-2))+1));out[0x10]=idx&255;return out
  else:
   low=f(q-f(inv*h))
   if low<=1:
    idx=max(mn,int(f(f(low*f(n-2))+1)));hi=int(f(f(q*f(n-2))+1))
    if idx!=old and old!=hi:out[0x10]=idx&255
    return out
  out[0x10]=(n-1)&255;return out
 out[0x10]=mn&255
 size=struct.unpack_from('<f',unit,0x14)[0]
 for j in range(n,0,-1):
  if size<struct.unpack_from('<f',rec,8+j*4)[0]:out[0x10]=j&255;break
 return out

def main():
 e=GUC();rng=random.Random(3788760)
 unit=e.alloc(0x40);rec=e.alloc(0x80);sphere=e.alloc(0x20);extra=e.alloc(4)
 cases=8192
 for k in range(cases):
  n=k%9;mn=(k//9)%3;mode=(k//27)%2;held=(k//54)%5==0;external=(k//270)%7==0
  base=f(rng.uniform(-300,300));depth=f(rng.uniform(-500,80));radius=f(rng.uniform(0,80));bias=(0.,25.,-10.)[(k//3)%3];h=(0.,10.,2.)[(k//7)%3]
  start,end=(20.,50.) if k%3 else (100.,100.)
  inv=f(1/(end-start)) if start!=end else 1.
  rb=bytearray(0x80);put(rb,0,start);put(rb,4,2*start-end);put(rb,8,inv)
  for j in range(3,12):put(rb,j*4,f(2**(-j+1)))
  put(rb,0x5c,radius)
  ub=bytearray(rng.randbytes(0x40));ub[0x10]=k%9;ub[0x11]=int(held);put(ub,0x14,rng.uniform(0,1));put(ub,0x18,depth)
  struct.pack_into('<Q',ub,8,extra if external else unit+0x10)
  if external:ub[0x1f]=k%255;e.mu.mem_write(extra,bytes([ub[0x1f]]))
  expect=ref(ub,rb,unit+0x10,base,mn,n,mode,bias,h)
  e.mu.mem_write(unit,bytes(ub));e.mu.mem_write(rec,bytes(rb));e.mu.mem_write(sphere,bytes(rb[0x50:0x70]))
  e.mu.mem_write(0x7105999d58,bytes([mode]));e.f32(0x7105999d5c,bias);e.f32(0x7105999d60,h)
  e.call(0x7103788760,unit,mn,n,rec,0,sphere,fargs=(base,))
  got=bytes(e.mu.mem_read(unit,0x40))
  assert got==expect,(k,got.hex(),expect.hex(),base,depth,radius,bias,h,n,mn,mode)
 # Whole static draw packet path, real original selector, original false metadata leaf.
 model=e.alloc(0x320);mi=e.alloc(0x30);vh=e.alloc(0x20);vt=e.alloc(0x18);views=e.alloc(0x7f0);camera=e.alloc(0x110);packet=e.alloc(0x30);scene=e.alloc(0x5000);mask=e.alloc(4);opts=e.alloc(4)
 e.wq(model+0x30,mi);e.wq(model+0x38,rec);e.wq(model+0x58,sphere);e.wq(model+0xd0,vt);e.wq(vt+0x10,0x710112d234)
 e.mu.mem_write(model+0x22,bytes([0,3,0]));e.mu.mem_write(opts,bytes([4]));e.wq(views+0x18,camera)
 e.f32(camera+0x28,1);e.f32(camera+0xf8,1)
 packet_cases=2048
 for k in range(packet_cases):
  d=f(rng.uniform(1,250));r=f(rng.uniform(.25,20));bias=(0.,25.)[k%2];base=f(rng.uniform(-10,10));old=k%3;off=k%3
  b=bytearray(0x80);put(b,0,20);put(b,4,-10);put(b,8,f(1/30));struct.pack_into('<Q',b,0x38,rec+0x40);b[0x40]=old
  e.mu.mem_write(rec,bytes(b));e.f32(sphere,0);e.f32(sphere+4,0);e.f32(sphere+8,-d);e.f32(sphere+0xc,r);e.f32(views+8,base)
  e.mu.mem_write(model+0x24,bytes([off]));e.mu.mem_write(packet,bytes(0x30));e.u32(mask,1)
  e.mu.mem_write(0x7105999d58,bytes([1]));e.f32(0x7105999d5c,bias);e.f32(0x7105999d60,10)
  exp_rec=bytearray(b);put(exp_rec,0x44,f(f(r*-1)/f(-d)));put(exp_rec,0x48,-d)
  ur=bytearray(exp_rec[0x30:0x70]);rb=bytearray(exp_rec);put(rb,0x5c,r)
  rr=ref(ur,rb,rec+0x40,base,0,3,1,bias,10);exp_rec[0x40]=rr[0x10];struct.pack_into('<I',exp_rec,0x30,7)
  ep=bytearray(0x30);put(ep,0,struct.unpack_from('<f',exp_rec,0x44)[0]);struct.pack_into('<II',ep,4,7,7);struct.pack_into('<Q',ep,0x10,views);struct.pack_into('<I',ep,0x18,7);struct.pack_into('<I',ep,0x20,0xf7ffffff);ep[0x25]=exp_rec[0x40];ep[0x26]=min(2,off+exp_rec[0x40]);put(ep,0x28,f(-d+r))
  ret=e.call(0x7103777f28,model,views,1,packet,scene,mask,opts,0)
  got=bytes(e.mu.mem_read(packet,0x30));gr=bytes(e.mu.mem_read(rec,0x80))
  assert got==ep,(k,'packet',got.hex(),ep.hex())
  assert gr==exp_rec,(k,'record',gr.hex(),exp_rec.hex())
  assert ret==1,(k,'ret',ret)
 assert not e.plt_stubbed,e.plt_stubbed
 out={'selector_cases':cases,'static_packet_cases':packet_cases,'mismatch':0,'algorithm_stubs':[],'plt_stubs':e.plt_stubbed,'scope':'original selector entire64B and static3777f28 entire48Bpacket+128Brecord; finite inputs; dynamic per-shape producer read only; GPU unexecuted'}
 (R/'analysis/completion/r8/lod_emu.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
