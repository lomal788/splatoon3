"""Phive 충돌 레이어 필터 표(Default/Other=상대팀/Same=같은팀)에서 탄 레이어 행을 뽑는다.
입력 analysis/gimmick/PhiveConfig.json ([gimmick] 산출물), 출력 analysis/combat/layer_filter_bullet.json
사용: PY web/tools/combat_layers.py [레이어명...]
"""
import json, sys
R = 'C:/dev/splatoon3'
d = json.load(open(R + '/analysis/gimmick/PhiveConfig.json', encoding='utf-8'))
L = d['LayerEntityCollection']
names = sys.argv[1:] or ['SplInkBullet', 'SplInkBullet_FriendThrough', 'SplPlayer']
out = {}
for tset in ['LayerEntityParamTableSet', 'LayerEntityParamTableSetOther', 'LayerEntityParamTableSetSame']:
    T = d[tset]['Default']['LayerEntityFilterTable']
    out[tset] = {}
    for n in names:
        i = L.index(n)
        row = {L[j]: T[i][j] for j in range(len(L))}
        col = {L[j]: T[j][i] for j in range(len(L))}
        out[tset][n] = {'row': row, 'symmetric': row == col}
        print(tset, n, 'symmetric' if row == col else 'ASYM')
        print('   ', ' '.join(f'{k}={v}' for k, v in row.items() if v))
json.dump({'layers': L, 'tables': out}, open(R + '/analysis/combat/layer_filter_bullet.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
