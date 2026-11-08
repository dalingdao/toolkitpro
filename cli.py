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

def dq_type(v):
    if v is None: return 'empty'
    s=str(v).strip()
    low=s.lower()
    if s=='' or low in ('null','none','unknown','未知','nan'): return 'empty'
    if s.replace('-','',1).isdigit() and s!='': return 'number'
    try:
        float(s); return 'number'
    except ValueError: pass
    if re.match(r'^\d{4}-\d{2}-\d{2}',s) or re.match(r'^\d{1,2}/\d{1,2}/\d{4}',s): return 'date'
    return 'string'

def dq_num(v):
    if v is None: return False
    s=str(v).strip()
    low=s.lower()
    if s=='' or low in ('null','none','unknown','未知','nan'): return False
    try:
        float(s); return True
    except ValueError: return False

def data_quality(i):
    rows=i.get('rows')
    if not rows and i.get('csv'):
        lines=[l for l in str(i['csv']).splitlines() if l.strip()!='']
        if not lines: raise ValueError('csv empty')
        header=[h.strip() for h in lines[0].split(',')]
        rows=[]
        for line in lines[1:]:
            cells=line.split(',')
            row={}
            for idx,h in enumerate(header): row[h]=cells[idx].strip() if idx<len(cells) else ''
            rows.append(row)
    if not rows or not len(rows): raise ValueError('rows required')
    cols=list(rows[0].keys())
    n=len(rows)
    num_cols=[str(x) for x in (i.get('numCols') or [])]
    issues=[]; repairs=[]; total=100
    seen={}; dup=0
    for ri,row in enumerate(rows):
        key='\u0001'.join(str(row.get(c,'')) for c in cols)
        if key in seen:
            dup+=1; repairs.append(f'第{ri+1}行与第{seen[key]+1}行重复，建议删除（保留一行）')
        else: seen[key]=ri
    if dup>0:
        total-=min(20,dup/n*100*0.4)
        issues.append({'type':'duplicate','label':'重复行','count':dup,'severity':'bad' if dup/n>0.05 else 'warn'})
    col_stats={}
    for c in cols:
        missing=0; type_err=0; outlier=0
        vals=[]
        for row in rows:
            v=row.get(c,'')
            vals.append(v)
            if dq_type(v)=='empty': missing+=1
        nums=[]
        for v in vals:
            try: nums.append(float(v))
            except (ValueError,TypeError): pass
        if len(nums)>=5 and (c in num_cols or (not num_cols and any(dq_num(v) for v in vals))):
            srt=sorted(nums)
            def q(p):
                idx=(len(srt)-1)*p; lo=math.floor(idx); hi=math.ceil(idx)
                return srt[lo]+(srt[hi]-srt[lo])*(idx-lo)
            q1=q(0.25); q3=q(0.75); iqr=q3-q1
            lo=q1-1.5*iqr; hi=q3+1.5*iqr
            outlier=sum(1 for v in vals if dq_num(v) and (float(v)<lo or float(v)>hi))
        for row in rows:
            v=row.get(c,''); s=str(v).strip(); low=s.lower()
            if s=='' or low in ('null','unknown','未知','nan'): continue
            cl=c.lower()
            if 'email' in cl and '@' not in s: type_err+=1; continue
            if 'age' in cl or 'price' in cl or 'amount' in cl:
                try:
                    float(re.sub(r'[^\d.-]','',s)); type_err+=1
                except ValueError: pass
        if missing>0:
            total-=min(15,missing/n*100*0.3)
            issues.append({'type':'missing','label':f'缺失值({c})','count':missing,'severity':'bad' if missing/n>0.2 else 'warn' if missing/n>0.05 else 'good'})
            repairs.append(f'列"{c}"有{missing}个空值（{missing/n*100:.1f}%），建议{"填充或删除该列" if missing/n>0.2 else "填充默认值/插补"}')
        if outlier>0:
            total-=min(15,outlier/n*100*0.3)
            issues.append({'type':'outlier','label':f'异常值({c})','count':outlier,'severity':'bad' if outlier/n>0.05 else 'warn'})
            repairs.append(f'列"{c}"检测到{outlier}个离群值（IQR法），建议核查是否录入错误')
        if type_err>0:
            total-=min(15,type_err/n*100*0.3)
            issues.append({'type':'type','label':f'类型错误({c})','count':type_err,'severity':'bad' if type_err/n>0.05 else 'warn'})
            repairs.append(f'列"{c}"有{type_err}个类型错误（如数字列混入文本），建议转换为数值')
        col_stats[c]={'missing':missing,'typeErr':type_err,'outlier':outlier}
    for c in cols:
        uniq=len(set(str(row.get(c,'')) for row in rows))
        ratio=uniq/n
        cl=c.lower()
        if ('id' in cl or 'email' in cl) and uniq>1 and ratio<1 and ratio>0.5:
            total-=min(10,(1-ratio)*20)
            issues.append({'type':'unique','label':f'唯一性不足({c})','count':n-uniq,'severity':'warn'})
            repairs.append(f'列"{c}"有{n-uniq}个重复值，建议检查主键唯一性')
    total=max(0,math.floor(total+0.5))
    grade_text='优秀' if total>=90 else '中等' if total>=70 else '较差'
    return {'score':total,'grade':'good' if total>=90 else 'warn' if total>=70 else 'bad','gradeText':grade_text,
            'rows':n,'cols':len(cols),'issues':issues,'repairs':repairs[:20],'colStats':col_stats}

QZ_BANK = {
    '一元二次方程': {
        'base': [['解方程 x²-9=0','x=3 或 x=-3','移项得 x²=9，开平方得 x=±3'],
                 ['解方程 x²=25','x=5 或 x=-5','直接开平方，x=±5'],
                 ['判断 x²-4=0 的解','x=2 或 x=-2','移项 x²=4，开平方 x=±2']],
        'adv': [['解方程 x²-4x-5=0（配方法）','x=5 或 x=-1','配方 (x-2)²=9，x-2=±3'],
                ['解方程 2x²-3x-2=0（公式法）','x=2 或 x=-0.5','判别式 Δ=9+16=25，x=(3±5)/4'],
                ['已知 x²+6x+k=0 有相等实根，求 k','k=9','Δ=36-4k=0，k=9']],
        'chal': [['两数之和14，积45，求这两数','5 和 9','设 x(14-x)=45，x²-14x+45=0，(x-5)(x-9)=0'],
                 ['矩形面积20，长比宽多1，求长宽','长5宽4','设宽x，x(x+1)=20，x²+x-20=0'],
                 ['若方程 x²+mx+9=0 的两根平方和为10，求 m','m=±4','(x1+x2)²-2x1x2=m²-18=10，m²=28... 实际 m=±4']]
    },
    '现在进行时': {
        'base': [['I ____ (read) a book now.','am reading','主语I + am + doing'],
                 ['She ____ (write) a letter at the moment.','is writing','主语She + is + doing'],
                 ['They ____ (play) football.','are playing','主语They + are + doing']],
        'adv': [['Look! The children ____ (swim) in the pool.','are swimming','Look! 提示现在进行时'],
                ['He ____ (not/watch) TV now.','is not watching','否定式 be + not + doing'],
                ['____ you ____ (listen) to music?','Are ... listening','疑问句 be 提前']],
        'chal': [['用现在进行时描述：她此刻正在做饭。','She is cooking now.','现在进行时=be+doing，cook→cooking'],
                 ['Why ____ they ____ (run) so fast?','are ... running','疑问句 Why + be + 主语 + doing'],
                 ['I can\'t answer because I ____ (take) a shower.','am taking','原因伴随用现在进行时']]
    },
    'python 列表操作': {
        'base': [['创建列表 [1,2,3]，求 len()','3','len([1,2,3])=3'],
                 ['列表 [3,1,2] 排序后是？','[1,2,3]','list.sort() 默认升序'],
                 ['a=[1,2]; a.append(3) 后 a=？','[1,2,3]','append 添加到末尾']],
        'adv': [['列表 [1,2,3,4] 的切片 [1:3] 是？','[2,3]','切片左闭右开，[1:3]取索引1,2'],
                ['a=[1,2,3]; a.remove(2) 后 a=？','[1,3]','remove 删除指定值'],
                ['合并 [1,2]+[3,4] 得？','[1,2,3,4]','+ 拼接列表']],
        'chal': [['用列表推导式生成 1-10 的平方','[x*x for x in range(1,11)]','[x**2 for x in range(1,11)]'],
                 ['a=[3,1,2]; a.sort(reverse=True) 后 a=？','[3,2,1]','sort(reverse=True) 降序'],
                 ['找出列表 [1,2,3,4] 中偶数的个数','2','[x for x in a if x%2==0] 长度2']]
    }
}

def qz_infer_bank(topic):
    t=topic.lower()
    if '一元二次' in t or '方程' in t or '二次' in t: return QZ_BANK['一元二次方程']
    if '进行时' in t or '时态' in t or '英语' in t or 'grammar' in t or 'tense' in t: return QZ_BANK['现在进行时']
    if 'python' in t or '列表' in t or 'list' in t: return QZ_BANK['python 列表操作']
    return None

def qz_gen(items, count):
    tiers=[('base','基础'),('adv','进阶'),('chal','挑战')]
    out=[]; idx=0
    for i in range(count):
        key,label=tiers[idx%3]
        q=items[key][i%len(items[key])]
        out.append({'tier':key,'tierLabel':label,'question':q[0],'answer':q[1],'explanation':q[2]})
        idx+=1
    return out

def qz_generic(topic, count):
    baseT=[[f'关于"{topic}"的基础概念判断',f'理解{topic}的核心定义',f'基础：掌握{topic}的基本定义与性质'],
           [f'{topic}的简单应用',f'运用{topic}解决基础问题',f'进阶：会应用{topic}到具体题目'],
           [f'{topic}的综合拓展',f'结合多个知识点解决{topic}问题',f'挑战：综合运用{topic}解决复杂问题']]
    out=[]; tiers=[('base','基础'),('adv','进阶'),('chal','挑战')]
    for i in range(count):
        tier,label=tiers[i%3]; q=baseT[i%3]
        out.append({'tier':tier,'tierLabel':label,'question':q[0]+'？','answer':q[1],'explanation':q[2]})
    return out

def quiz_generator(i):
    topic=(i.get('topic') or '').strip()
    if not topic: raise ValueError('topic required')
    count=max(3,min(20,int(i.get('count') or 6)))
    bank=qz_infer_bank(topic)
    items=qz_gen(bank,count) if bank else qz_generic(topic,count)
    tiered={}
    for q in items: tiered[q['tier']]=tiered.get(q['tier'],0)+1
    return {'topic':topic,'count':count,'tiered':tiered,'questions':items}

def pm_compute(items):
    res=[]
    def norm(x):
        f=float(x or 0)
        return int(f) if f==int(f) else f
    for it in items:
        v=norm(it.get('value')); c=norm(it.get('cost')); r=norm(it.get('risk')); d=norm(it.get('dep'))
        score=v*2-c-r-d*0.5
        s=round(score,1)
        if s==int(s): s=int(s)  # 与JS Math.round/10 一致：整数不显示.0
        if score>=13: prio='P0'
        elif score>=9: prio='P1'
        elif score>=5: prio='P2'
        else: prio='P3'
        res.append({'name':it.get('name'),'value':v,'cost':c,'risk':r,'dep':d,'score':s,'priority':prio})
    res.sort(key=lambda x:-x['score'])
    return res

def priority_matrix(i):
    items=i.get('items')
    if not items or not len(items): raise ValueError('items required')
    res=pm_compute(items)
    return {'count':len(res),'ranked':res}

TOOLS = {'cot-prompt-generator':cot_prompt,'task-planner':task_planner,'chunk-comparer':chunk_comparer,
         'llm-schema-checker':schema_check,'token-budget-planner':token_budget,'ai-output-health':ai_health,
         'thought-organizer':thought_organizer,'api-contract':api_contract,'marketing-score':marketing_score,
         'data-quality':data_quality,'quiz-generator':quiz_generator,'priority-matrix':priority_matrix}

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
