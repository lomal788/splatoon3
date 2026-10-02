"""XLink2 (ELink2 .belnk / SLink2 .bslnk) 파서 — Splatoon 3 v0 (XLNK version 0x22 / 0x1F).

Splatoon 2 기반 공개 디컴파일(Nitr4m12/xlink2, 32비트 위치)과 달리, 이 게임의 파일은
위치(pos) 필드가 64비트로 넓어진 배치다. 필드 배치는 원본 파일 전수 일관성 검사로 맞췄다.

사용:
  PY web/tools/effect_xlink.py info  <file.belnk|.zs>
  PY web/tools/effect_xlink.py check <file>
  PY web/tools/effect_xlink.py user  <file> <UserName> [--json out.json]
  PY web/tools/effect_xlink.py dump  <file> <out.json>          # 전 사용자(해시만 있는 이름은 hash로)
  PY web/tools/effect_xlink.py find  <file> <문자열>             # 에셋/액션/키 이름 부분 검색
"""
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(__file__))

# 컨테이너 종류(u8 @+0): 생성 0x710388e468 의 점프 표 0x7104af2b9c 로 판독. 5 는 Splatoon 2 참고 소스의 'Asset' 이 아니라
# 두 속성 값의 2차원 표로 자식을 고르는 컨테이너(start 0x7103890ca4 → 선택 0x71038909a4)라 'Grid' 로 부른다(이름은 웹 권장명) [판독].
# 3(Blend)은 +1 바이트가 0 이면 전 자식 재생(0x710388f59c), 0 이 아니면 값 범위 블렌드(0x710388e8fc, 데이터에는 없음).
CONTAINER_TYPES = ['Switch', 'Random', 'Random2', 'Blend', 'Sequence', 'Grid']
PARAM_TYPES = {0: 'UInt32', 1: 'Float', 2: 'Bool', 3: 'Enum', 4: 'String', 5: 'Arrange'}
REF_TYPES = ['Direct', 'String', 'Curve', 'Random', 'ArrangeGroup', 'Bitflag', 'Random2Pow', 'Random3Pow',
             'Random4Pow', 'Random1Point5Pow', 'Random2PowWeightMin', 'Random3PowWeightMin',
             'Random4PowWeightMin', 'Random1Point5PowWeightMin', 'Random2PowWeightMax',
             'Random3PowWeightMax', 'Random4PowWeightMax', 'Random1Point5PowWeightMax']
# 비교 연산 번호(조건 +5 u8) [판독]: Switch 자식 선택 0x71038978bc 가 '속성값 OP 조건값' 으로 비교한다.
# 0 ==, 1 >, 2 >=, 3 <, 4 <=, 5 != (정수형 속성은 32비트 정수 비교, F32 는 float 비교). 범위 밖 번호면 그 자식은 불일치.
COMPARE = ['Equal', 'GreaterThan', 'GreaterThanOrEqual', 'LessThan', 'LessThanOrEqual', 'NotEqual']
PROP_TYPES = ['Enum', 'S32', 'F32']


def load_bytes(path):
    d = open(path, 'rb').read()
    if path.endswith('.zs'):
        import zstandard
        d = zstandard.ZstdDecompressor().decompress(d, max_output_size=1 << 30)
    return d


def f32(u):
    return struct.unpack('<f', struct.pack('<I', u & 0xffffffff))[0]


class XLink:
    def __init__(self, data):
        self.d = d = data
        assert d[:4] == b'XLNK', d[:4]
        (self.size, self.version, self.numResParam, self.numResAssetParam, self.numTrigOw) = struct.unpack_from('<5I', d, 4)
        self.trigOwPos, self.lpnPos = struct.unpack_from('<QQ', d, 0x18)
        (self.numLPN, self.numLPEN, self.numDirect, self.numRandom, self.numCurve, self.numCurvePoint) = \
            struct.unpack_from('<6I', d, 0x28)
        self.exRegionPos, = struct.unpack_from('<Q', d, 0x40)
        self.numUser, = struct.unpack_from('<I', d, 0x48)
        self.condPos, self.namePos = struct.unpack_from('<QQ', d, 0x50)
        n = self.numUser
        self.userHashes = list(struct.unpack_from('<%dI' % n, d, 0x60))
        ob = (0x60 + 4 * n + 7) & ~7
        self.userOffsets = list(struct.unpack_from('<%dQ' % n, d, ob))
        self.pdtPos = ob + 8 * n
        self._parse_param_define()
        self._parse_common()

    # ---------- 공통 ----------
    def s(self, off):
        """이름표 오프셋 -> 문자열"""
        p = self.namePos + off
        e = self.d.index(b'\0', p)
        return self.d[p:e].decode('utf-8')

    def _parse_param_define(self):
        d = self.d
        b = self.pdtPos
        self.pdtSize, self.numUserParam, self.numAssetParam, self.numCustomAssetParam, self.numTriggerParam, _ = \
            struct.unpack_from('<6I', d, b)
        tot = self.numUserParam + self.numAssetParam + self.numTriggerParam
        ents = b + 0x18
        st = ents + tot * 0x18
        defs = []
        for i in range(tot):
            np_, ty, _pad, dv = struct.unpack_from('<QIIQ', d, ents + i * 0x18)
            nm = d[st + np_:d.index(b'\0', st + np_)].decode()
            if ty == 1:
                dflt = struct.unpack('<d', struct.pack('<Q', dv))[0]
            elif ty == 4:
                dflt = ''
            else:
                dflt = dv - (1 << 64) if dv >= 1 << 63 else dv
            defs.append({'name': nm, 'type': PARAM_TYPES.get(ty, ty), 'default': dflt})
        self.userParamDefs = defs[:self.numUserParam]
        self.assetParamDefs = defs[self.numUserParam:self.numUserParam + self.numAssetParam]
        self.triggerParamDefs = defs[self.numUserParam + self.numAssetParam:]
        self.assetTablePos = b + self.pdtSize

    def _parse_common(self):
        d = self.d
        # 에셋 파라미터 표: {u64 mask; u32 ResParam[popcount]} 반복, 정렬 없음
        p = self.assetTablePos
        self.assetParamAt = {}
        nparams = 0
        for i in range(self.numResAssetParam):
            mask, = struct.unpack_from('<Q', d, p)
            k = bin(mask).count('1')
            vals = struct.unpack_from('<%dI' % k, d, p + 8)
            self.assetParamAt[p - self.assetTablePos] = (mask, vals)
            p += 8 + 4 * k
            nparams += k
        self.assetTableEnd = p
        p = self.trigOwPos
        self.trigOwAt = {}
        for i in range(self.numTrigOw):
            mask, = struct.unpack_from('<I', d, p)
            k = bin(mask).count('1')
            vals = struct.unpack_from('<%dI' % k, d, p + 4)
            self.trigOwAt[p - self.trigOwPos] = (mask, vals)
            p += 4 + 4 * k
            nparams += k
        self.trigOwEnd = p
        self.countedResParam = nparams
        p = self.lpnPos
        self.lpnTable = list(struct.unpack_from('<%dQ' % self.numLPN, d, p)); p += 8 * self.numLPN
        self.lpenTable = list(struct.unpack_from('<%dQ' % self.numLPEN, d, p)); p += 8 * self.numLPEN
        self.directPos = p
        self.direct = list(struct.unpack_from('<%dI' % self.numDirect, d, p)); p += 4 * self.numDirect
        self.random = [struct.unpack_from('<2f', d, p + 8 * i) for i in range(self.numRandom)]; p += 8 * self.numRandom
        self.curves = []
        for i in range(self.numCurve):
            sp, npnt, ctype, isg, pname, pidx, lpidx = struct.unpack_from('<4HQih', d, p + 0x18 * i)
            self.curves.append({'pointStart': sp, 'numPoint': npnt, 'curveType': ctype, 'isPropGlobal': isg,
                                'prop': self.s(pname), 'propIdx': pidx, 'localPropertyNameIdx': lpidx})
        p += 0x18 * self.numCurve
        self.curvePoints = [struct.unpack_from('<2f', d, p + 8 * i) for i in range(self.numCurvePoint)]
        p += 8 * self.numCurvePoint
        self.commonEnd = p

    # ---------- 값 해석 ----------
    def resolve(self, raw, pdef):
        ref = raw >> 24
        v = raw & 0xffffff
        rname = REF_TYPES[ref] if ref < len(REF_TYPES) else ref
        ty = pdef['type']
        if ref == 0:  # Direct: direct value 표 인덱스
            u = self.direct[v]
            if ty == 'Float':
                return round(f32(u), 6)
            if ty == 'String':
                return self.s(u)
            if ty == 'Bool':
                return bool(u)
            return u - (1 << 32) if u >= 1 << 31 else u
        if ref == 1:  # String: 이름표 오프셋
            return self.s(v)
        if ref == 2:  # Curve
            c = dict(self.curves[v])
            c['points'] = [list(map(lambda x: round(x, 6), pt)) for pt in self.curvePoints[c['pointStart']:c['pointStart'] + c['numPoint']]]
            return {'curve': c}
        if ref == 3 or ref >= 6:
            lo, hi = self.random[v]
            return {rname: [round(lo, 6), round(hi, 6)]}
        return {rname: v}

    def params(self, mask, vals, defs):
        out = {}
        j = 0
        for bit in range(64):
            if mask >> bit & 1:
                pdef = defs[bit] if bit < len(defs) else {'name': 'bit%d' % bit, 'type': '?'}
                out[pdef['name']] = self.resolve(vals[j], pdef)
                j += 1
        return out

    # ---------- 사용자 ----------
    def user_index(self, name):
        h = zlib.crc32(name.encode())
        return self.userHashes.index(h) if h in self.userHashes else -1

    def parse_condition(self, off):
        d = self.d
        p = self.condPos + off
        ptype, = struct.unpack_from('<i', d, p)
        if ptype == 0:
            # 64비트판 Switch 조건: +4 u8 propertyType, +5 u8 compareType, +6 u8 isSolved, +7 u8 isGlobal,
            # +8 s32 localPropertyEnumNameIdx, Enum 이면 +0x10 u64 이름표 오프셋(0x18 B), 아니면 +0xC s32/f32 값(0x10 B)
            proptype, cmp_, solved, isg = d[p + 4:p + 8]
            enidx, = struct.unpack_from('<i', d, p + 8)
            c = {'parent': 'Switch', 'propertyType': PROP_TYPES[proptype] if proptype < 3 else proptype,
                 'compare': COMPARE[cmp_] if cmp_ < len(COMPARE) else cmp_}
            if proptype == 0:
                val, = struct.unpack_from('<Q', d, p + 0x10)
                c['value'] = self.s(val)
            elif proptype == 2:
                c['value'] = round(struct.unpack_from('<f', d, p + 0xc)[0], 6)
            else:
                c['value'] = struct.unpack_from('<i', d, p + 0xc)[0]
            c['localPropertyEnumNameIdx'] = enidx
            c['isGlobal'] = bool(isg)
            return c
        if ptype in (1, 2):
            _, w = struct.unpack_from('<if', d, p)
            return {'parent': CONTAINER_TYPES[ptype], 'weight': round(w, 6)}
        return {'parent': CONTAINER_TYPES[ptype] if 0 <= ptype < 6 else ptype}

    def user(self, idx):
        d = self.d
        u = self.userOffsets[idx]
        hdr = struct.unpack_from('<12I', d, u)
        (_setup, nLP, nCT, nAsset, nRC, nSlot, nAct, nActTrig, nProp, nPropTrig, nAlways, _pad) = hdr
        trigPos, = struct.unpack_from('<Q', d, u + 0x30)
        p = u + 0x38
        lps = [self.s(x) for x in struct.unpack_from('<%dQ' % nLP, d, p)]
        p += 8 * nLP
        uparams_raw = struct.unpack_from('<%dI' % self.numUserParam, d, p)
        p += 4 * self.numUserParam
        uparams = {}
        for i, raw in enumerate(uparams_raw):
            uparams[self.userParamDefs[i]['name']] = self.resolve(raw, self.userParamDefs[i])
        sorted_ids = struct.unpack_from('<%dH' % nCT, d, p)
        p += 2 * nCT
        p = (p + 3) & ~3  # numCallTable 홀수면 u16 하나 채움(4 정렬)
        ctPos = p
        cts = []
        for i in range(nCT):
            (kp, aid, flag, dur, parent, guid, khash, _p2, psp, cdp) = struct.unpack_from('<QhHiiIIIqq', d, p + 0x30 * i)
            ct = {'i': i, 'key': self.s(kp), 'assetId': aid, 'flag': flag, 'duration': dur, 'parent': parent,
                  'guid': '%08x' % guid}
            if khash != zlib.crc32(self.s(kp).encode()):
                ct['keyHashMismatch'] = '%08x' % khash
            if cdp != 0xffffffff and cdp != -1:
                ct['condition'] = self.parse_condition(cdp)
            ct['_psp'] = psp
            cts.append(ct)
        contPos = ctPos + 0x30 * nCT
        for ct in cts:
            psp = ct.pop('_psp')
            if ct['flag'] & 1:
                if psp == -1 or psp == 0xffffffff:
                    ct['container'] = None
                    continue
                q = contPos + psp
                ctype = d[q]
                cs, ce = struct.unpack_from('<ii', d, q + 4)
                c = {'type': CONTAINER_TYPES[ctype], 'children': [cs, ce]}
                if ctype == 3 and d[q + 1]:
                    c['valueBlend'] = d[q + 1]
                if ctype == 0:
                    wp, wid, lpi, isg = struct.unpack_from('<QihB', d, q + 0x10)
                    c.update({'watchProperty': self.s(wp), 'watchPropertyId': wid, 'localPropertyNameIdx': lpi,
                              'isGlobal': bool(isg)})
                    if d[q + 0x1f]:
                        # +0x1f != 0: 속성이 아니라 액션 슬롯(이름 = watchProperty, 예 Skl[0]) 의 현재 액션 번호를
                        # 조건 +8 정수와 비교(0 ==, 5 != 만 의미 있음) [판독 0x71038978bc]
                        c['watchActionSlot'] = True
                elif ctype == 5:
                    # Grid: +0x10/+0x18 u64 속성 이름 2개, +0x20/+0x22 s16 로컬 속성 이름 인덱스, +0x24 u16 bit0/bit1 = 각 속성 전역,
                    # +0x26/+0x27 u8 값 개수 n1/n2, +0x28 u32 값[n1+n2] (전역=이름표 오프셋, 로컬=localPropertyEnumNameRef 인덱스),
                    # 뒤 s32 자식[n1*n2] (행=속성1 값, 열=속성2 값, -1 없음) [판독 0x71038909a4 + 데이터]
                    p1, p2 = struct.unpack_from('<QQ', d, q + 0x10)
                    i1, i2, gfl, n1, n2 = struct.unpack_from('<hhHBB', d, q + 0x20)
                    vals = struct.unpack_from('<%dI' % (n1 + n2), d, q + 0x28)
                    tab = struct.unpack_from('<%di' % (n1 * n2), d, q + 0x28 + 4 * (n1 + n2))

                    def ename(v, glob):
                        return self.s(v) if glob else self.s(self.lpenTable[v])
                    c.update({'props': [self.s(p1), self.s(p2)], 'propIsGlobal': [bool(gfl & 1), bool(gfl & 2)],
                              'values1': [ename(v, gfl & 1) for v in vals[:n1]],
                              'values2': [ename(v, gfl & 2) for v in vals[n1:]],
                              'table': [list(tab[r * n2:(r + 1) * n2]) for r in range(n1)]})
                ct['container'] = c
            else:
                if psp in self.assetParamAt:
                    mask, vals = self.assetParamAt[psp]
                    ct['params'] = self.params(mask, vals, self.assetParamDefs)
                else:
                    ct['paramsError'] = psp
        q = u + trigPos
        slots = []
        for i in range(nSlot):
            np_, a0, a1 = struct.unpack_from('<Qhh', d, q + 0x10 * i)
            slots.append({'name': self.s(np_), 'actions': [a0, a1]})
        q += 0x10 * nSlot
        acts = []
        for i in range(nAct):
            np_, t0, t1 = struct.unpack_from('<Qii', d, q + 0x10 * i)
            acts.append({'name': self.s(np_), 'triggers': [t0, t1]})
        q += 0x10 * nAct
        atrigs = []
        for i in range(nActTrig):
            raw = d[q + 0x28 * i:q + 0x28 * (i + 1)]
            guid, _a, ctb = struct.unpack_from('<IIQ', raw)
            t = self._trig_common(ctb, ctPos, cts)
            w = struct.unpack_from('<10I', raw)
            t.update({'guid': '%08x' % guid, 'raw': ['%08x' % x for x in w[4:]]})
            atrigs.append(t)
        q += 0x28 * nActTrig
        props = []
        for i in range(nProp):
            wp, isg, t0, t1, _p = struct.unpack_from('<QiiiI', d, q + 0x18 * i)
            props.append({'watchProperty': self.s(wp), 'isGlobal': isg, 'triggers': [t0, t1]})
        q += 0x18 * nProp
        ptrigs = []
        for i in range(nPropTrig):
            # 0x20 B: +0 guid, +4 u16 flag, +6 s16 overwriteHash, +8 u64 assetCtbPos, +0x10 u64 conditionPos,
            # +0x18 s32 overwriteParamPos, +0x1c pad
            raw = d[q + 0x20 * i:q + 0x20 * (i + 1)]
            guid, flag, owh, ctb, cond, owp = struct.unpack_from('<IHhQQi', raw)
            t = self._trig_common(ctb, ctPos, cts)
            t['condition'] = self.parse_condition(cond)
            t.update({'guid': '%08x' % guid, 'flag': flag, 'overwriteHash': owh & 0xffff})
            if owp != -1:
                t['overwrite'] = self.trig_overwrite(owp)
            ptrigs.append(t)
        q += 0x20 * nPropTrig
        always = []
        for i in range(nAlways):
            # 0x18 B: +0 guid, +4 u16 flag, +6 s16 overwriteHash, +8 u64 assetCtbPos, +0x10 s32 overwriteParamPos
            raw = d[q + 0x18 * i:q + 0x18 * (i + 1)]
            guid, flag, owh, ctb, owp = struct.unpack_from('<IHhQi', raw)
            t = self._trig_common(ctb, ctPos, cts)
            t.update({'guid': '%08x' % guid, 'flag': flag, 'overwriteHash': owh & 0xffff})
            if owp != -1:
                t['overwrite'] = self.trig_overwrite(owp)
            always.append(t)
        q += 0x18 * nAlways
        return {
            'hash': '%08x' % self.userHashes[idx], 'offset': u,
            'counts': {'localProperty': nLP, 'callTable': nCT, 'asset': nAsset, 'randomContainer': nRC,
                       'actionSlot': nSlot, 'action': nAct, 'actionTrigger': nActTrig, 'property': nProp,
                       'propertyTrigger': nPropTrig, 'alwaysTrigger': nAlways},
            'localProperties': lps, 'userParams': uparams, 'sortedCallTableIdx': list(sorted_ids),
            'callTables': cts, 'actionSlots': slots, 'actions': acts, 'actionTriggers': atrigs,
            'properties': props, 'propertyTriggers': ptrigs, 'alwaysTriggers': always, '_end': q - u,
        }

    def trig_overwrite(self, off):
        if off in self.trigOwAt:
            mask, vals = self.trigOwAt[off]
            return self.params(mask, vals, self.triggerParamDefs)
        return {'error': off}

    def _trig_common(self, ctb, ctPos, cts):
        if ctb % 0x30 == 0 and 0 <= ctb // 0x30 < len(cts):
            i = ctb // 0x30
            return {'callTable': i, 'key': cts[i]['key']}
        return {'callTableError': ctb}


def flatten_tree(user, root_i):
    """콜 테이블 i 아래 트리(컨테이너 → 자식) 를 펼친다."""
    cts = user['callTables']

    def rec(i, depth):
        ct = cts[i]
        node = {k: v for k, v in ct.items() if k not in ('i',)}
        if ct.get('container'):
            a, b = ct['container']['children']
            node['childrenNodes'] = [rec(j, depth + 1) for j in range(a, b + 1)]
        return node
    return rec(root_i, 0)


def main():
    cmd = sys.argv[1]
    x = XLink(load_bytes(sys.argv[2]))
    if cmd == 'info':
        print(json.dumps({'version': x.version, 'numUser': x.numUser, 'numResParam': x.numResParam,
                          'countedResParam': x.countedResParam, 'numResAssetParam': x.numResAssetParam,
                          'assetTable': [hex(x.assetTablePos), hex(x.assetTableEnd)], 'trigOwPos': hex(x.trigOwPos),
                          'trigOwEnd': hex(x.trigOwEnd), 'lpnPos': hex(x.lpnPos), 'commonEnd': hex(x.commonEnd),
                          'exRegionPos': hex(x.exRegionPos), 'condPos': hex(x.condPos), 'namePos': hex(x.namePos),
                          'userParams': x.userParamDefs, 'assetParams': x.assetParamDefs,
                          'numCustomAssetParam': x.numCustomAssetParam, 'triggerParams': x.triggerParamDefs},
                         ensure_ascii=False, indent=1))
    elif cmd == 'check':
        ok = True
        print('ResParam count', x.numResParam, x.countedResParam)
        print('assetTableEnd==trigOwPos', x.assetTableEnd == x.trigOwPos, 'trigOwEnd==lpnPos', x.trigOwEnd == x.lpnPos,
              'commonEnd==exRegion', x.commonEnd == x.exRegionPos)
        ends = []
        errs = 0
        for i in range(x.numUser):
            try:
                us = x.user(i)
            except Exception as e:
                errs += 1
                print('user', i, 'ERR', e)
                continue
            nxt = sorted(o for o in x.userOffsets if o > x.userOffsets[i])
            lim = nxt[0] if nxt else x.condPos
            if x.userOffsets[i] + us['_end'] != lim:
                ends.append((i, hex(x.userOffsets[i] + us['_end']), hex(lim)))
            for ct in us['callTables']:
                if 'paramsError' in ct or 'keyHashMismatch' in ct:
                    errs += 1
            for t in us['actionTriggers'] + us['propertyTriggers'] + us['alwaysTriggers']:
                if 'callTableError' in t:
                    errs += 1
        print('users', x.numUser, 'end mismatches', len(ends), ends[:5], 'errors', errs)
    elif cmd == 'user':
        i = x.user_index(sys.argv[3])
        if i < 0:
            print('not found'); return
        us = x.user(i)
        us['name'] = sys.argv[3]
        s = json.dumps(us, ensure_ascii=False, indent=1)
        if '--json' in sys.argv:
            open(sys.argv[sys.argv.index('--json') + 1], 'w', encoding='utf-8').write(s)
        else:
            print(s)
    elif cmd == 'dump':
        names = {}
        if len(sys.argv) > 4:
            for n in open(sys.argv[4], encoding='utf-8').read().split():
                names[zlib.crc32(n.encode())] = n
        out = {}
        for i in range(x.numUser):
            us = x.user(i)
            out[names.get(x.userHashes[i], '#%08x' % x.userHashes[i])] = us
        json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print('users', len(out), 'named', sum(1 for k in out if not k.startswith('#')))
    elif cmd == 'find':
        pat = sys.argv[3]
        for i in range(x.numUser):
            us = x.user(i)
            for ct in us['callTables']:
                blob = json.dumps(ct, ensure_ascii=False)
                if pat in blob:
                    print('#%08x' % x.userHashes[i], ct['i'], ct['key'], ct.get('params', {}).get('AssetName', ''))


if __name__ == '__main__':
    main()
