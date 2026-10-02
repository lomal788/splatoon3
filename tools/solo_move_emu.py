"""Original solo movement subfunctions, finite f32 inputs, no game/impl writes.
Reuse prior original initializers and Unicorn image loader. Outputs analysis/completion/.
The k enumeration table is synthetic; no runtime gear acquisition is asserted.
SM branches for non-shooter weapons are deliberately excluded.
"""
import json, random, struct
from pathlib import Path
import numpy as np
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_S0, UC_ARM64_REG_PC
from player_gear_emu import GearEmu, HEAP, fbits
from network_uc import UC, STACK
from disasm import disasm
from xref import load_img, BASE
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/completion'
f=np.float32

def add(a,b): return f(f(a)+f(b))
def sub(a,b): return f(f(a)-f(b))
def mul(a,b): return f(f(a)*f(b))
def dot(a,b): return add(add(mul(a[0],b[0]),mul(a[1],b[1])),mul(a[2],b[2]))
def norm(a,reverse=False):
    q=[mul(v,v) for v in a]
    return f(np.sqrt(add(q[2],add(q[1],q[0])) if reverse else add(add(q[0],q[1]),q[2])))
def plane(a,n):
    d=dot(a,n)
    return [sub(x,mul(y,d)) for x,y in zip(a,n)]
def positive_plane(a,n):
    return plane(a,n) if dot(a,n)<0 else a

def k_cases():
    e=GearEmu(); pp=HEAP; tbl=HEAP+0x8100
    constant=e.rd(0x71058c0348); rows=[]
    rng=random.Random(20261002)
    for table in ([100,101,102,103,104,105], [104,100], [100,101,104], [103,105]):
        e.uc.mem_write(tbl,b''.join(struct.pack('<i',v) for v in table))
        e.uc.mem_write(0x71058bc378,struct.pack('<I',len(table)))
        index=table.index(104) if 104 in table else 0
        bit=(table[index]-100)&31
        for flags in [0,1<<4,0xffffffff,1<<bit]+[rng.getrandbits(32) for _ in range(64)]:
            for arg in (0,1,2,3):
                e.uc.mem_write(pp+0xac,struct.pack('<I',flags))
                e.uc.reg_write(UC_ARM64_REG_X0,pp); e.uc.reg_write(UC_ARM64_REG_X1,arg)
                result=e.run(0x710266c6e4)
                assert result is True,result
                got=e.uc.reg_read(UC_ARM64_REG_S0)
                expected=fbits(1 if arg&1 or not (flags>>bit)&1 else constant)
                rows.append(dict(table=table,flags=hex(flags),arg=arg,got=hex(got),expected=hex(expected)))
                assert got==expected,rows[-1]
    return dict(count=len(rows),mismatches=0,constant=float(constant),constant_bits=hex(fbits(constant)),rows=rows)

def sm_cases():
    e=UC(); b=e.alloc(0xb000); pc=e.alloc(0xe600); result=e.alloc(0x1800)
    actor=e.alloc(0x400); component=e.alloc(0x200)
    c=json.loads((ROOT/'analysis/player/bss_consts_58bb000.json').read_text(encoding='utf-8'))['0x71058bbda8']
    e.u32(0x71058bbda8,c['u32'])
    smooth_step=struct.unpack('<f',struct.pack('<I',c['u32']))[0]
    def ptr(a,v): e.mu.mem_write(a,struct.pack('<Q',v))
    def vec(a,v): e.mu.mem_write(a,struct.pack('<3f',*map(float,v)))
    rng=random.Random(20261003); rows=[]
    cases=[]
    # First four expose zero, clamp, support-plane and saved-velocity paths.
    for raw in ([0,0,0],[.06,.08,0],[.1,-.2,.3],[.05,.1,.2]):
        cases.append(dict(d=list(raw),normal=[0,1,0],secondary=[0,1,0],a=[0,0,0],ext=[0,0,0],command=[0,0,0],jump=[0,0,0],saved=[.1,.2,.3],ratio=0,skip=False,fast=False,extra=[0,0,0],extra_active=False))
    for i in range(2000):
        v=lambda: [f(rng.uniform(-.2,.2)) for _ in range(3)]
        cases.append(dict(d=v(),normal=rng.choice([[0,1,0],[1,0,0],[0,0,1],[.6,.8,0]]),secondary=rng.choice([[0,1,0],[1,0,0],[0,.6,.8]]),a=v(),ext=v() if i%3 else [0,0,0],command=v(),jump=v(),saved=v(),ratio=f(rng.random()),skip=bool(i%2),fast=bool(i%11==0),extra=v(),extra_active=bool(i%4==0)))
    for ix,c in enumerate(cases):
        e.mu.mem_write(b,b'\0'*0xb000); e.mu.mem_write(component,b'\0'*0x200)
        ptr(b+8,actor); ptr(b+0xa690,pc); ptr(pc+0xe378,result); ptr(b+0xa698,component)
        e.mu.mem_write(b+0xfa5,bytes([c['fast']]))
        e.mu.mem_write(result+0x1746,b'\0')
        vec(b+0x10,c['d']); vec(b+0x40,[0,0,0]); vec(b+0x180,c['normal']); vec(b+0x34,c['secondary'])
        vec(b+0xfc,c['a']); vec(b+0x108,c['ext']); vec(b+0x114,c['command']); vec(b+0x750,c['jump']); vec(b+0x120,c['saved'])
        e.f32(b+0x178,c['ratio']); e.u32(b+0xad8,1 if c['skip'] else 0)
        e.mu.mem_write(component+0x39,bytes([c['extra_active']])); vec(component+0x3c,c['extra'])
        e.mu.mem_write(STACK+0xf0000,struct.pack('<3Q',b+0x474,b+0x750,b+0xe4))
        e.call(0x710246d060,b+0xa600,b+0x10,b+0x180,b+0xad0,component,0,0,b+0xa2c)
        got=e.mu.reg_read(UC_ARM64_REG_S0); gotratio=e.ru32(b+0x178)
        ratio=f(c['ratio'])
        if c['fast']:
            expected=norm(c['saved']); newratio=ratio
        else:
            d=plane(c['d'],c['normal'])
            adjusted=plane([sub(x,add(y,z)) for x,y,z in zip(c['d'],c['a'],c['ext'])],c['normal'])
            command=plane([add(x,y) for x,y in zip(c['command'],c['jump'])],c['normal'])
            if not c['skip']:
                d=positive_plane(d,c['secondary']); adjusted=positive_plane(adjusted,c['secondary']); command=positive_plane(command,c['secondary'])
            speed=norm(d,True); limit=norm(command,True)
            newratio=add(ratio,mul(sub(1 if dot(c['ext'],c['ext'])>0 else 0,ratio),.2))
            if newratio>f(.01):
                dest=norm(adjusted,True); step=mul(newratio,smooth_step)
                speed=max(sub(speed,step),dest) if dest<=speed else min(add(speed,step),dest)
            speed=min(speed,limit)
            expected=add(speed,norm(c['extra'])) if c['extra_active'] else speed
        row=dict(case=ix,fast=c['fast'],skip_secondary=c['skip'],got=hex(got),expected=hex(fbits(expected)),ratio_got=hex(gotratio),ratio_expected=hex(fbits(newratio)))
        rows.append(row)
        assert got==fbits(expected) and gotratio==fbits(newratio),row
    return dict(count=len(rows),mismatches=0,smoothing_step=float(smooth_step),rows=rows,excluded=['non-shooter charge compensation','NaN libm fallback','runtime component/field provenance'])

def main():
    OUT.mkdir(exist_ok=True)
    m=load_img()
    for name,addr,size in [('squid_speed_k',0x710266c6e4,340),('sm_move_speed',0x710246d060,1436)]:
        lines=disasm(m,addr-BASE,end=addr-BASE+size)
        (OUT/(name+'.asm')).write_text('\n'.join(hex(BASE+p)+' '+s+' '+n for p,s,n in lines)+'\n',encoding='utf-8')
    for name,fn in [('squid_speed_k',k_cases),('sm_move_speed',sm_cases)]:
        result=fn()
        (OUT/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf-8')
        print(name+': '+str(result['count'])+' cases, mismatches='+str(result['mismatches']))
if __name__=='__main__': main()
