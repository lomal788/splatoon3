"""Original bit11 setter/staging apply -> native body-pair filter; synthetic engine/native wrapper fixture, original table values reused r7."""
import json,random,struct
from pathlib import Path
from r6_player_uc import PUC
u=PUC();T=u.alloc(0x400);Q=u.alloc(0x30);W=u.alloc(0x400);N=u.alloc(8*0xc0);Pairs=u.alloc(32*8);B=[];F=[];S=[]
u.wq(W+0x38,N);u.wq(Q+0x20,T)
D=json.loads(Path('analysis/completion/r7/physics_table_emu.json').read_text(encoding='utf8'))
tables=[t['items']['Default']['allow'] for t in D['tables']]
for off,rows in zip((0x10,0x90,0x110),tables):u.mu.mem_write(T+off,struct.pack('<29I',*rows))
for i in range(8):
 b=u.alloc(0x400);f=u.alloc(0x40);s=u.alloc(0xd8);B.append(b);F.append(f);S.append(s)
 u.wq(b,0x71057468d8);u.wq(b+0x80,s);u.wq(b+0x180,f);u.wq(N+i*0xc0+0x98,b);u.wq(b+0x88,4)
rng=random.Random(0x8c56);mismatch=[];samples=[];cases=0;fields=0
for i in range(2048):
 for j in range(8):
  u.mu.mem_write(F[j],bytes(0x40));u.mu.mem_write(S[j],bytes(0xd8));u.wq(B[j]+0x88,4)
  layer=rng.randrange(29);sub=rng.randrange(27);mask=rng.getrandbits(32);submask=rng.getrandbits(32);group=rng.randrange(3);kind=rng.choice([0,0x10000])
  u.w32(F[j]+8,layer|(sub<<6)|kind);u.w32(F[j]+0xc,mask);u.w32(F[j]+0x10,submask);u.w32(B[j]+0x15c,mask);u.mu.mem_write(F[j]+0x30,struct.pack('<H',group))
  enabled=rng.randrange(2) # bit11=1 disables permission
  e1=u.call(0x7103ae4c48,B[j],enabled)
  before=(u.r32(S[j]+0xd4),u.r32(S[j]+0xd0))
  e2=u.call(0x7103b07b8c,S[j],B[j],0,0,0,0,0,0)
  got=(u.rq(B[j]+0x88)>>11&1,u.r32(F[j]+0xc));exp=(enabled,0 if enabled else mask)
  if e1 or e2 or got!=exp:mismatch.append(dict(i=i,body=j,label='apply',errors=[e1,e2],got=got,expected=exp,pending=before))
  fields+=2
 inp=[(rng.randrange(8),rng.randrange(8)) for k in range(rng.randrange(1,17))]
 u.mu.mem_write(Pairs,b''.join(struct.pack('<II',a,b) for a,b in inp));expected=[]
 for a,b in inp:
  wa,wb=(u.r32(F[x]+8) for x in (a,b));la,lb=wa&63,wb&63;sa,sb=wa>>6&31,wb>>6&31
  ga,gb=(struct.unpack('<H',u.mu.mem_read(F[x]+0x30,2))[0] for x in (a,b));tab=0 if not ga or not gb else 1 if ga==gb else 2
  allowed=(tables[tab][la]>>lb&1) and (u.r32(F[a]+0xc)>>lb&1) and (u.r32(F[b]+0xc)>>la&1)
  if allowed and not ((wa&0xf0000)==0x10000 or (wb&0xf0000)==0x10000):allowed=(u.r32(F[a]+0x10)>>sb&1) and (u.r32(F[b]+0x10)>>sa&1)
  if allowed:expected.append((a,b))
 e=u.call(0x7103c56bc4,Q,W,Pairs,len(inp));n=u.x(0);got=[struct.unpack('<II',u.mu.mem_read(Pairs+8*k,8)) for k in range(min(n,32))]
 if e or got!=expected:mismatch.append(dict(i=i,label='pair',error=e,input=inp,got=got,expected=expected))
 if i<3:samples.append(dict(input=inp,result=got))
 cases+=len(inp)
r=dict(batch=2048,staging_cases=2048*8,staging_fields=fields,pair_cases=cases,mismatch=mismatch,samples=samples,null={str(k):v for k,v in u.null_calls.items()},auto=u.auto_pages,faults=u.faults,plt=u.plt_stubbed,scope=__doc__,unverified=['native broadphase registration refresh3c50020 when attached','form shape resizing','full native solver'])
Path('analysis/completion/r8/physics_bit11_pair_emu.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r,ensure_ascii=False))
