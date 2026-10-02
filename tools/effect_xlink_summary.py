"""덤프 JSON(effect_xlink.py dump 결과)에서 사용자 하나를 사람이 읽기 쉬운 줄 형식으로 요약.
사용: PY web/tools/effect_xlink_summary.py <users.json> <UserName|#hash>
"""
import json, sys
U = json.load(open(sys.argv[1], encoding='utf-8'))
u = U[sys.argv[2]]
print('counts', u['counts'], 'localProps', u['localProperties'])
if u['userParams']:
    print('userParams', json.dumps(u['userParams'], ensure_ascii=False))
for c in u['callTables']:
    head = '%2d %-28s parent=%-3s' % (c['i'], c['key'], c['parent'])
    if c.get('container'):
        k = c['container']
        print(head, 'CONTAINER', k['type'], k['children'], k.get('watchProperty', ''), '(G)' if k.get('isGlobal') else '')
    else:
        cond = c.get('condition')
        cs = ''
        if cond:
            cs = 'if %s %s' % (cond.get('compare', ''), cond.get('value', cond.get('weight')))
        print(head, cs, json.dumps(c.get('params'), ensure_ascii=False))
for s in u['actionSlots']:
    print('SLOT', s['name'], s['actions'])
for a in u['actions']:
    ts = u['actionTriggers'][a['triggers'][0]:a['triggers'][1] + 1] if a['triggers'][0] >= 0 else []
    print('  ACTION', a['name'], '->', [(t['key'], t['raw'][0], t['raw'][2], t['raw'][3]) for t in ts])
for p in u['properties']:
    ts = u['propertyTriggers'][p['triggers'][0]:p['triggers'][1] + 1]
    print('PROPERTY', p['watchProperty'], '(G)' if p['isGlobal'] else '', '->',
          [(t['key'], t['condition'].get('compare'), t['condition'].get('value')) for t in ts])
for t in u['alwaysTriggers']:
    print('ALWAYS', t['key'], t.get('overwrite', ''))
