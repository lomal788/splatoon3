"""Execute original classifier + actual WeaponSp RTTI up to first B65c write.

Type guards are supplied as already-initialized synthetic input bytes. Actual
type virtual methods and parent IsA execute; binding/weapon actions do not.
"""
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *
from network_uc import UC, BASE, STACK, STUB

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/camera_100_r10/state'


def main():
    table = json.loads((OUT/'classifier_data.json').read_text(encoding='utf-8'))['table']
    uc = UC()
    mu = uc.mu
    w = uc.alloc(0xb000)
    actor = uc.alloc(0x800)
    component = uc.alloc(0x400)
    stack = STACK+0xe0000
    guards = [int(row['token'],16)+8 for row in table]
    guards += [BASE+g for g in [0x58d62d8,0x58d5178,0x58c6c78,0x5801640,0x5801650]]
    for guard in guards:
        mu.mem_write(guard,b'\x01')
    # Exact native store sites; hook stops AFTER the selected store instruction.
    stores = {int(row['writer'],16) for row in table}|{BASE+0x2494b94}
    ends = {pc+4 for pc in stores}
    entries = {int(row['actor_IsA'],16) for row in table}|{BASE+0x289c0a0}
    state = {}
    cases = []

    def audit(m,address,size,_):
        if STUB <= address < STUB+0x1000 or BASE+0x3e90000 <= address < BASE+0x3e9e000:
            raise AssertionError(('unexpected stub/PLT',hex(address)))
        if address in entries:
            state['actual_rtti_calls'] += 1
        if address in ends:
            state['stop'] = address
            m.emu_stop()

    mu.hook_add(UC_HOOK_CODE,audit)
    inputs = [dict(name=row['label'],vt=int(row['actor']['vtable'],16),expected=row['runtime_code'])
              for row in table]
    inputs.append(dict(name='ordinary WeaponShooter unmatched',vt=BASE+0x5652468,expected=0))
    prior_values = [0,10,11,18,0xffffffff]
    for input_row in inputs:
        for prior in prior_values:
            mu.mem_write(actor,struct.pack('<Q',input_row['vt']))
            mu.mem_write(w+0xd4,struct.pack('<I',prior))
            mu.mem_write(stack,b'\0'*0x200)
            for reg in range(UC_ARM64_REG_X0,UC_ARM64_REG_X28+1):
                mu.reg_write(reg,0)
            mu.reg_write(UC_ARM64_REG_X20,component)
            mu.reg_write(UC_ARM64_REG_X22,w)
            mu.reg_write(UC_ARM64_REG_X24,component)
            mu.reg_write(UC_ARM64_REG_X25,actor)
            mu.reg_write(UC_ARM64_REG_X29,STACK+0xef000)
            mu.reg_write(UC_ARM64_REG_SP,stack)
            state.clear()
            state.update(stop=None,actual_rtti_calls=0)
            mu.emu_start(BASE+0x249368c,BASE+0x2494fb0,count=20000)
            assert state['stop'] in ends, (input_row,state)
            actual = struct.unpack('<I',bytes(mu.mem_read(w+0xd4,4)))[0]
            assert actual == input_row['expected'], (input_row,prior,actual,state)
            cases.append(dict(name=input_row['name'],actual_actor_vt=hex(input_row['vt']),
                              prior_code=prior,expected=actual,output=actual,
                              selected_writer=hex(state['stop']-4),
                              actual_rtti_calls=state['actual_rtti_calls']))
    # Only the original selection gate: reaching skip target proves that this
    # classification write is bypassed, not what later whole-function updates do.
    gate_cases = []
    for name,current,old,end in [('null',0,actor,0x249353c),
                                 ('same_primary',actor,actor,0x2493554)]:
        for prior in prior_values:
            frame = STACK+0xef000
            mu.mem_write(w+0xd4,struct.pack('<I',prior))
            mu.mem_write(frame-0x48,b'\0'*0x48)
            mu.reg_write(UC_ARM64_REG_X22,w)
            mu.reg_write(UC_ARM64_REG_X24,old)
            mu.reg_write(UC_ARM64_REG_X25,current)
            mu.reg_write(UC_ARM64_REG_X29,frame)
            mu.emu_start(BASE+0x2493430,BASE+end,count=10)
            assert mu.reg_read(UC_ARM64_REG_PC) == BASE+end
            actual = struct.unpack('<I',bytes(mu.mem_read(w+0xd4,4)))[0]
            assert actual == prior
            gate_cases.append(dict(gate=name,prior=prior,output=actual,skip_target=hex(BASE+end)))
    result = dict(scope='original classifier368c→firstB65cstore plus actual actorVT/RTTI; '
                        'typeguard-ready synthetic bytes; no binding/special actions or whole249257c',
                  counts={'classifier_prefix':len(cases),'selection_skip_gate':len(gate_cases)},mismatch=0,
                  function_stubs=0,sdk_stubs=0,plt_stubs=0,arbitrary_math_stubs=0,
                  guard_inputs=[hex(g) for g in guards],cases=cases,gate_cases=gate_cases)
    (OUT/'classifier_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(counts=result['counts'],mismatch=0,
                          actual_rtti_calls=sum(r['actual_rtti_calls'] for r in cases))))


if __name__ == '__main__':
    main()
