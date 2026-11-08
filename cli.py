#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ToolkitPro CLI - Python unified command-line interface
Usage:
  python cli.py <tool> --input '<json>'       # inline (bash ok)
  python cli.py <tool> --input-file <path>    # from file (cross-platform)
Output: JSON {"tool":..., "input":..., "output":...}
Logic mirrors cli.js (and each tool page JS) exactly.
"""
import json, re, sys, math

# ---- cot-prompt-generator ----
ROLE = {'general':'严谨的通用推理专家','writing':'资深内容创作者','analysis':'资深分析师',
        'coding':'资深软件工程师','learning':'耐心的高效教学专家'}

def cot_build(task, sc, dep):
    role = ROLE.get(sc, ROLE['general'])
    if sc == 'writing':
        steps = ['1. 理解目标：明确这篇内容要传达的核心信息与受众。',
                 '2. 拆解结构：想清楚引言-论点-论据-收尾的骨架。',
                 '3. 找亮点：列出能打动受众的具体事实/故事/数字。',
                 '4. 起草：按骨架逐段成文，用具体代替抽象。',
                 '5. 打磨：删掉空话，检查逻辑连贯与节奏。',
                 '6. 质量检查：是否达成了目标？是否够具体？能否更有冲击力？']
    elif sc == 'analysis':
        steps = ['1. 明确问题：要回答的核心问题是什么？',
                 '2. 收集证据：有哪些关键数据/事实/假设？',
                 '3. 多角度推理：从正反/成本/风险多角度分析。',
                 '4. 权衡：列出各方案的利弊与适用条件。',
                 '5. 结论与依据：给出明确结论，并说明依据与不确定性。',
                 '6. 质量检查：结论是否有数据支撑？是否忽略关键反例？']
    elif sc == 'coding':
        steps = ['1. 明确需求：要实现的输入/输出/边界条件。',
                 '2. 选方案：权衡简单/性能/可维护，选最合适的。',
                 '3. 逐步实现：先骨架后细节，每步保持可运行。',
                 '4. 边界处理：空值/异常/极端输入。',
                 '5. 自测：用典型与边界用例验证。',
                 '6. 质量检查：代码是否简洁？有无隐患？是否可维护？']
    elif sc == 'learning':
        steps = ['1. 诊断：学习者已掌握什么，卡在哪。',
                 '2. 拆解：把知识点拆成可理解的小步。',
                 '3. 类比：用熟悉事物解释新概念。',
                 '4. 循序渐进：先概念后应用，先易后难。',
                 '5. 检验：出小练习确认理解。',
                 '6. 质量检查：学习者能否用自己的话复述？能否应用？']
    else:
        steps = ['1. 明确目标：最终要得到什么结果。',
                 '2. 拆解：把问题分成可处理的子问题。',
                 '3. 信息需求：需要哪些信息/假设？',
                 '4. 推理：逐层推理，每一步基于上一步。',
                 '5. 结论：给出明确结论与依据。',
                 '6. 质量检查：结论是否合理？有无逻辑漏洞？']
    steps_txt = '\n'.join(steps[:3] if dep == 'brief' else steps)
    return (f'你是一名{role}。\n\n## 任务\n{task}\n\n'
            f'## 请按以下思维链逐步推理（每一步都写出来，再进入下一步）：\n{steps_txt}\n\n'
            '## 约束\n- 不要凭空臆测；信息不足时明确说明并给出所需假设。\n'
            '- 每个结论必须说明依据。\n- 语言清晰、具体、可执行，避免空话。\n'
            '- 若任务有歧义，先列出你的理解并确认。\n\n'
            '## 输出格式\n- 先给结论要点，再给详细分析。\n- 分点输出，关键处加粗。\n'
            '- 最后给"质量自检"：我的推理是否有漏洞？哪些地方最不确定？')

def cot_prompt(i):
    task = (i.get('task') or '').strip()
    if not task: raise ValueError('task required')
    return {'scenario': i.get('scenario','general'),
            'prompt': cot_build(task, i.get('scenario','general'), i.get('depth','detail')),
            'steps': 6}

# ---- task-planner ----
STEP_NAMES = ['明确范围与验收标准','收集信息与需求','设计核心方案','实现核心内容','验证与修复','交付与复盘']
def task_planner(i):
    goal = (i.get('goal') or '').strip()
    if not goal: raise ValueError('goal required')
    n = int(i.get('steps') or 6); bud = int(i.get('budget') or 100000); ci = float(i.get('ci') or 3)
    tasks = [round((bud/(n*(n+1)/2))*(n-k)) for k in range(n)]
    total = sum(tasks)
    return {'steps':[{'step':k+1,'name':STEP_NAMES[k] if k < len(STEP_NAMES) else f'推进步骤{k+1}','budget':t}
                     for k,t in enumerate(tasks)],
            'total_budget':total,'total_cost':round(total/1e6*ci,4),'currency':'USD'}

# ---- chunk-comparer ----
def est_tok(s):
    cjk = len(re.findall(r'[\u4e00-\u9fff]', s))
    return math.ceil(cjk*1.5 + (len(s)-cjk)/4)
def chunk_comparer(i):
    text = i.get('text') or ''
    if not text: raise ValueError('text required')
    cs = int(i.get('chunk') or 500); ov = int(i.get('overlap') or 50); sem = int(i.get('sem') or 3)
    ln = len(text); tot = est_tok(text)
    char_chunks = max(1, math.ceil((ln-ov)/(cs-ov)))
    paras = [p for p in re.split(r'\n+', text) if p.strip()]
    rec = 0; cur = 0
    for p in paras:
        if cur + len(p) > cs and cur > 0: rec += 1; cur = 0
        cur += len(p) + 1
    if cur > 0: rec += 1
    sents = [s for s in re.split(r'[。！？.!?]+', text) if s.strip()]
    sem_chunks = max(1, math.ceil(len(sents)/sem))
    m = min(char_chunks, rec, sem_chunks)
    return {'char_chunks':char_chunks,'recursive_chunks':rec,'semantic_chunks':sem_chunks,
            'total_tokens':tot,'recommended':'char' if m==char_chunks else 'recursive' if m==rec else 'semantic'}

# ---- llm-schema-checker ----
def type_of(v):
    if v is None: return 'null'
    if isinstance(v, list): return 'array'
    if isinstance(v, bool): return 'boolean'
    if isinstance(v, int): return 'number'
    if isinstance(v, float): return 'number'
    return type(v).__name__
def schema_check(i):
    data = json.loads(i.get('data') or '{}'); s = json.loads(i.get('schema') or '{}')
    req = s.get('required', []); props = s.get('properties', {}); errors = []
    for k in req:
        if k not in data: errors.append({'field':k,'error':'missing','expect':props.get(k,{}).get('type')})
        elif k in props and props[k].get('type') and type_of(data[k]) != props[k]['type']:
            errors.append({'field':k,'error':'type','expect':props[k]['type'],'got':type_of(data[k])})
    return {'valid':len(errors)==0,'errors':errors}

# ---- token-budget-planner ----
def token_budget(i):
    bud = int(i.get('budget') or 200000)
    ws = [x for x in i.get('weights',[2,3,3,4]) if x > 0]
    ns = i.get('names') or []
    tot = sum(ws)
    return {'total':bud,'alloc':[{'step':ns[k] if k < len(ns) else k+1,'budget':round(bud*w/tot),'pct':round(w/tot*100)}
                                 for k,w in enumerate(ws)],'remain':0}

# ---- ai-output-health ----
def ai_health(i):
    req = (i.get('req') or '').strip(); out = (i.get('out') or '').strip()
    if not out: raise ValueError('out required')
    ol, rl = len(out), len(req)
    coverage = min(100, round((ol/rl)*50)) if req else 50
    vague = len(re.findall(r'可能|大概|也许|或许|据说|我认为|我觉得|应该|maybe|probably|might|I think', out))
    factual = max(0, 100-vague*12)
    turn = len(re.findall(r'但是|然而|不过|however|but|yet', out))
    consist = max(0, 100-turn*8)
    struct = len(re.findall(r'^#{1,6} |^[-*•] |^\d+\.', out, re.M))
    clarity = min(100, 40+struct*10+max(0, 60-round(ol/40)))
    total = round((coverage+factual+consist+clarity)/4)
    return {'score':total,'coverage':coverage,'factual':factual,'consist':consist,'clarity':clarity,
            'grade':'A' if total>=85 else 'B' if total>=70 else 'C' if total>=50 else 'D'}

# ---- thought-organizer ----
def thought_build(idea, sc):
    goal = f'把"{idea}"变成可执行的清晰目标，明确最终要交付什么、给谁、怎么判断成功。'
    aud = '学习者本人（从零到掌握）' if sc=='learning' else '目标读者' if sc=='writing' else '目标用户/受众'
    if sc=='learning':
        mods = ['核心概念（要掌握什么）','知识地图（前置知识/依赖）','练习路径（由易到难）','检验（能否应用/复述）']
        steps = ['诊断起点','拆解知识点','安排练习节奏','检验掌握']
    elif sc=='writing':
        mods = ['核心论点（一句话说清）','论据链（事实/案例/数字）','结构（引言-展开-收尾）','受众共鸣点']
        steps = ['定核心论点','列论据','搭结构','打磨']
    else:
        mods = ['核心功能/价值（解决什么）','用户路径（从看到用）','关键模块（最小可行）','增长点（如何扩散）']
        steps = ['定义最小可行版本','搭核心模块','验证用户路径','迭代扩散']
    return (f'## 目标\n{goal}\n\n## 受众\n{aud}\n\n## 核心模块\n'
            + '\n'.join(f'{i+1}. {m}' for i,m in enumerate(mods))
            + '\n\n## 行动步骤\n' + '\n'.join(f'{i+1}. {s}' for i,s in enumerate(steps))
            + '\n\n## 检验标准\n- 是否清晰回答了"为什么值得做"？\n- 最小可行版本能否在较短时间内落地？\n- 用户/读者能否一眼理解价值？\n- 哪些部分最不确定、需先验证？')

def thought_organizer(i):
    idea = (i.get('idea') or '').strip()
    if not idea: raise ValueError('idea required')
    return {'scene': i.get('scene','creative'), 'framework': thought_build(idea, i.get('scene','creative'))}

# ---- api-contract ----
def api_infer(v):
    if v is None: return {'type':'null'}
    if isinstance(v, list): return {'type':'array','items': api_infer(v[0]) if v else {'type':'string'}}
    if isinstance(v, bool): return {'type':'boolean'}
    if isinstance(v, (int,float)): return {'type':'number'}
    if isinstance(v, str): return {'type':'string'}
    return {'type':'object','properties':{k:api_infer(v[k]) for k in v},'required':list(v.keys())}
def api_contract(i):
    rq = json.loads(i['req']) if i.get('req') else None
    rs = json.loads(i['res']) if i.get('res') else None
    if rq is None and rs is None: raise ValueError('req or res required')
    out = {}
    if rq is not None: out['request'] = {'contract': json.dumps(api_infer(rq), ensure_ascii=False, indent=2)}
    if rs is not None: out['response'] = {'contract': json.dumps(api_infer(rs), ensure_ascii=False, indent=2)}
    return out

# ---- marketing-score ----
def marketing_score(i):
    t=(i.get('title') or '').strip(); d=(i.get('desc') or '').strip()
    if not t: raise ValueError('title required')
    ln=len(t); platform=i.get('platform') or 'ecommerce'
    ranges={'ecommerce':[10,30],'social':[5,15],'email':[15,40]}
    r=ranges.get(platform, ranges['ecommerce'])
    if ln<r[0]: len_score=max(0,100-(r[0]-ln)*8)
    elif ln>r[1]: len_score=max(0,100-(ln-r[1])*4)
    else: len_score=100
    kw=[x for x in re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}|[0-9]+',t) if len(x)>=2]
    kw_score=min(100,len(kw)*15+20)
    emo=len(re.findall(r'超值|新品|爆款|限时|免费|省|划算|独家|升级|热销|全新|惊喜|优惠|立减|赠送',t+d))
    emo_score=min(100,40+emo*15)
    cta=len(re.findall(r'立即|点击|下单|咨询|了解|购买|加入|领取|抢购|预约',t+d))
    cta_score=min(100,30+cta*20)
    score=round(len_score*0.3+kw_score*0.25+emo_score*0.2+cta_score*0.25)
    sugg=[]
    if len_score<70: sugg.append(f'标题长度建议{r[0]}-{r[1]}字（当前{ln}字）')
    if kw_score<70: sugg.append('加入具体关键词（品牌/品类/数字/卖点）')
    if emo_score<70: sugg.append('加入情感触发词（超值/新品/限时/立减）')
    if cta_score<70: sugg.append('加入行动号召（立即/下单/咨询/领取）')
    return {'score':score,'grade':'A' if score>=85 else 'B' if score>=70 else 'C' if score>=50 else 'D',
            'lenScore':len_score,'kwScore':kw_score,'emoScore':emo_score,'ctaScore':cta_score,
            'length':ln,'suggestions':sugg,'platform':platform}

TOOLS = {'cot-prompt-generator':cot_prompt,'task-planner':task_planner,'chunk-comparer':chunk_comparer,
         'llm-schema-checker':schema_check,'token-budget-planner':token_budget,'ai-output-health':ai_health,
         'thought-organizer':thought_organizer,'api-contract':api_contract,'marketing-score':marketing_score}

# ---- entry ----
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    args = sys.argv[1:]
    if not args:
        print(json.dumps({'error':'no tool. Available: '+', '.join(TOOLS)}, ensure_ascii=False)); return 1
    tool = args[0]
    if tool not in TOOLS:
        print(json.dumps({'tool':tool,'error':'unknown tool. Available: '+', '.join(TOOLS)}, ensure_ascii=False)); return 1
    inp = {}
    if '--input-file' in args:
        try:
            with open(args[args.index('--input-file')+1], encoding='utf-8') as f: inp = json.load(f)
        except Exception as e:
            print(json.dumps({'tool':tool,'error':f'invalid --input-file: {e}'}, ensure_ascii=False)); return 1
    elif '--input' in args:
        try: inp = json.loads(args[args.index('--input')+1])
        except Exception as e:
            print(json.dumps({'tool':tool,'error':f'invalid --input JSON: {e}'}, ensure_ascii=False)); return 1
    try:
        out = TOOLS[tool](inp)
        print(json.dumps({'tool':tool,'input':inp,'output':out}, ensure_ascii=False, indent=2)); return 0
    except Exception as e:
        print(json.dumps({'tool':tool,'error':str(e)}, ensure_ascii=False)); return 1

if __name__ == '__main__':
    sys.exit(main())
