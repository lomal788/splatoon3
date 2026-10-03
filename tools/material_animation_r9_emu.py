"""Execute original FRES curve float/int readers on selected actual FMAA channels.

FMAA curve descriptors use the original decoded key/frame bytes and metadata.
No curve math is stubbed. The skin holder test separately supplies initialized
handles and captures material-update calls; it is not SDK material/GPU execution.
"""
from pathlib import Path
import json,struct,sys,hashlib
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_X0,UC_ARM64_REG_PC,UC_ARM64_REG_LR
sys.path.insert(0,str(Path(__file__).resolve().parent))
from r5_gfx_char_uc import GUC

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/port_graphics_r9/material_anim'
F32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
BITS=lambda x:struct.unpack('<I',struct.pack('<f',x))[0]

def descriptor(u,c):
    fr=c['frames']; flat=[v for k in c['keys'] for v in k]
    ft={'Single':0,'Decimal10x5':1,'Byte':2}[c['frameType']]
    fb=struct.pack('<'+'f'*len(fr),*fr) if ft==0 else struct.pack('<'+'H'*len(fr),*[int(v*32) for v in fr]) if ft==1 else bytes(int(v) for v in fr)
    kt=c['keyType']; it=c['type']=='StepInt'
    if kt=='Single':kb=struct.pack('<'+'I'*len(flat),*[int(v)&0xffffffff for v in flat]) if it else struct.pack('<'+'f'*len(flat),*flat)
    else:kb=struct.pack('<'+('h' if kt=='Int16' else 'b')*len(flat),*[int(v) for v in flat])
    fp=u.alloc(len(fb)+16);kp=u.alloc(len(kb)+16);p=u.alloc(48)
    u.mu.mem_write(fp,fb);u.mu.mem_write(kp,kb)
    u.wq(p,fp);u.wq(p+8,kp)
    u.mu.mem_write(p+16,struct.pack('<HHIffffII',c['flags'],len(fr),int(c['target'],16),c['start'],c['end'],c['scale'],c['offset'],c['deltaInt']&0xffffffff,0))
    return p

def main():
    d=json.loads((OUT/'material_channels.proposed.json').read_text(encoding='utf-8'))
    u=GUC();samples=[]; faults=[]
    for src,g in d['groups'].items():
      for a in g['clips']:
       for mat in a['materials']:
        for ci,c in enumerate(mat['curves']):
         if c['type'] not in ['Cubic','Linear','StepInt']:continue
         p=descriptor(u,c);cache=u.alloc(16)
         frames=sorted(set([-1.,0.,.125,.5,a['frames']+.5,c['end'],c['end']+1.]+[float(v) for v in c['frames']]+[F32((v+w)/2) for v,w in zip(c['frames'],c['frames'][1:])]+[F32(v+.125) for v in c['frames'] if v+.125<=c['end']]))
         for f in frames:
          u.mu.mem_write(cache,struct.pack('<fIII',float('inf'),0,0,0))
          try:
           r=u.call(0x710088e4b0 if c['type']=='StepInt' else 0x710088e380,p,cache,fargs=(f,))
           got=r&0xffffffff if c['type']=='StepInt' else u.mu.reg_read(UC_ARM64_REG_S0)&0xffffffff
           samples.append({'group':src,'clip':a['name'],'material':mat['material'],'curve':ci,'frame':f,'result':got,'integer':c['type']=='StepInt'})
          except Exception as e:faults.append({'group':src,'clip':a['name'],'curve':ci,'frame':f,'error':str(e),'pc':hex(u.mu.reg_read(UC_ARM64_REG_PC))})
    # Initialized Color_Skin holder, original range/FrameCount reader.
    calls=[];stubs={0x7101262c18:'anim_apply',0x7103673874:'model_flags',0x7103674288:'model_material',0x7103673fd0:'model_skeletal'}
    def hook(mu,addr,size,user):
      calls.append(stubs[addr]);mu.reg_write(UC_ARM64_REG_PC,mu.reg_read(UC_ARM64_REG_LR))
    for pc in stubs:u.mu.hook_add(UC_HOOK_CODE,hook,begin=pc,end=pc)
    holder=u.alloc(0x400);anim=u.alloc(0x80);model=u.alloc(0x100);res=u.alloc(0x200);handles=u.alloc(0x300);ents=u.alloc(0x18*4);fmaa=u.alloc(0x80);p1=u.alloc(0x10)
    u.wq(holder+0x40,anim);u.wq(holder+0x28,model);u.wq(model+0x58,res);u.wq(model+0x60,0);u.mu.mem_write(anim+8,b'\x01')
    u.u32(res+0x48,0x10);u.wq(res+0x50,handles);u.u32(handles+0x2a0,(2<<16)|1);u.mu.mem_write(res+0xa0,struct.pack('<H',1));u.u32(res+0x90,4);u.wq(res+0x98,ents);u.wq(ents+0x18*3,p1);u.wq(p1,fmaa)
    skin=[]
    for count in [9,1,0,21]:
     u.u32(fmaa+0x58,count)
     for idx in list(range(-3,count+4))+[-0x80000000,0x7fffffff]:
      u.u32(holder+0x38,0x5a5a5a5a);u.u32(anim+0x1c,0x7fc0dead);calls.clear()
      u.call(0x71014522b0,holder,idx&0xffffffff)
      skin.append({'frames':count,'index':idx,'holder':u.ru32(holder+0x38),'frameBits':u.ru32(anim+0x1c),'calls':list(calls)})
    target=ROOT/'web/games/splatoon3/tests/fixtures/material_animation_r9_native.json'
    result={'sourceSHA256':hashlib.sha256((ROOT/'extracted/exefs/main.reloc.img').read_bytes()).hexdigest(),'samples':samples,'skin':skin,'faults':faults,'pltStubs':list(set(u.plt_stubbed)),'scope':'whole float/int curve readers on actual keys; independent initialized Color_Skin holder with four apply/update capture callbacks; not whole ASB/frame/GPU'}
    target.write_text(json.dumps(result,separators=(',',':'))+'\n',encoding='utf-8')
    summary={'curveSamples':len(samples),'skinCases':len(skin),'faults':len(faults),'pltStubs':result['pltStubs'],'curveFunctions':['0x710088e380','0x710088e4b0'],'scope':result['scope']}
    (OUT/'native_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary));sys.exit(1 if faults or u.plt_stubbed else 0)

if __name__=='__main__':main()
