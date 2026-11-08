#!/usr/bin/env node
/* ToolkitPro CLI - unified command-line interface
 * Usage: node cli.js <tool> --input '<json>'
 * Example: node cli.js cot-prompt-generator --input '{"task":"帮我写一篇产品介绍","scenario":"writing"}'
 * Output: JSON {"tool":..., "input":..., "output":...}
 * Compute logic mirrors each tool's page JS exactly.
 */
'use strict';

// ---- cot-prompt-generator ----
const ROLE={general:'严谨的通用推理专家',writing:'资深内容创作者',analysis:'资深分析师',coding:'资深软件工程师',learning:'耐心的高效教学专家'};
function cotBuild(task,sc,dep){
  const role=ROLE[sc]||ROLE.general;
  const steps=sc==='writing'?[
'1. 理解目标：明确这篇内容要传达的核心信息与受众。',
'2. 拆解结构：想清楚引言-论点-论据-收尾的骨架。',
'3. 找亮点：列出能打动受众的具体事实/故事/数字。',
'4. 起草：按骨架逐段成文，用具体代替抽象。',
'5. 打磨：删掉空话，检查逻辑连贯与节奏。',
'6. 质量检查：是否达成了目标？是否够具体？能否更有冲击力？']:
sc==='analysis'?[
'1. 明确问题：要回答的核心问题是什么？',
'2. 收集证据：有哪些关键数据/事实/假设？',
'3. 多角度推理：从正反/成本/风险多角度分析。',
'4. 权衡：列出各方案的利弊与适用条件。',
'5. 结论与依据：给出明确结论，并说明依据与不确定性。',
'6. 质量检查：结论是否有数据支撑？是否忽略关键反例？']:
sc==='coding'?[
'1. 明确需求：要实现的输入/输出/边界条件。',
'2. 选方案：权衡简单/性能/可维护，选最合适的。',
'3. 逐步实现：先骨架后细节，每步保持可运行。',
'4. 边界处理：空值/异常/极端输入。',
'5. 自测：用典型与边界用例验证。',
'6. 质量检查：代码是否简洁？有无隐患？是否可维护？']:
sc==='learning'?[
'1. 诊断：学习者已掌握什么，卡在哪。',
'2. 拆解：把知识点拆成可理解的小步。',
'3. 类比：用熟悉事物解释新概念。',
'4. 循序渐进：先概念后应用，先易后难。',
'5. 检验：出小练习确认理解。',
'6. 质量检查：学习者能否用自己的话复述？能否应用？']:
[
'1. 明确目标：最终要得到什么结果。',
'2. 拆解：把问题分成可处理的子问题。',
'3. 信息需求：需要哪些信息/假设？',
'4. 推理：逐层推理，每一步基于上一步。',
'5. 结论：给出明确结论与依据。',
'6. 质量检查：结论是否合理？有无逻辑漏洞？'];
  const brief=dep==='brief';
  const stepsTxt=brief?steps.slice(0,3).join('\n'):steps.join('\n');
  return `你是一名${role}。

## 任务
${task}

## 请按以下思维链逐步推理（每一步都写出来，再进入下一步）：
${stepsTxt}

## 约束
- 不要凭空臆测；信息不足时明确说明并给出所需假设。
- 每个结论必须说明依据。
- 语言清晰、具体、可执行，避免空话。
- 若任务有歧义，先列出你的理解并确认。

## 输出格式
- 先给结论要点，再给详细分析。
- 分点输出，关键处加粗。
- 最后给"质量自检"：我的推理是否有漏洞？哪些地方最不确定？`;
}
function cotPrompt(input){
  const task=(input.task||'').trim();
  if(!task) throw new Error('task required');
  const sc=input.scenario||'general', dep=input.depth||'detail';
  return {scenario:sc,prompt:cotBuild(task,sc,dep),steps:6};
}

// ---- task-planner ----
function taskStepName(i){
  return ['明确范围与验收标准','收集信息与需求','设计核心方案','实现核心内容','验证与修复','交付与复盘'][i]||`推进步骤${i+1}`;
}
function taskPlanner(input){
  const goal=(input.goal||'').trim();
  if(!goal) throw new Error('goal required');
  const n=+input.steps||6,bud=+input.budget||100000,ci=+input.ci||3;
  const tasks=[];
  for(let i=0;i<n;i++){tasks.push(Math.round((bud/(n*(n+1)/2))*(n-i)))}
  return {steps:tasks.map((t,i)=>({step:i+1,name:taskStepName(i),budget:t})),total_budget:tasks.reduce((a,b)=>a+b,0),total_cost:tasks.reduce((a,b)=>a+b,0)/1e6*ci,currency:'USD'};
}

// ---- chunk-comparer ----
function estTok(s){const cjk=(s.match(/[\u4e00-\u9fff]/g)||[]).length;return Math.ceil(cjk*1.5+(s.length-cjk)/4)}
function chunkComparer(input){
  const text=input.text||'';
  if(!text) throw new Error('text required');
  const cs=+input.chunk||500,ov=+input.overlap||50,sem=+input.sem||3;
  const len=text.length,totTok=estTok(text);
  const charChunks=Math.max(1,Math.ceil((len-ov)/(cs-ov)));
  const paras=text.split(/\n+/).filter(x=>x.trim());
  let recChunks=0,cur=0;for(const p of paras){if(cur+p.length>cs&&cur>0){recChunks++;cur=0}cur+=p.length+1}if(cur>0)recChunks++;
  const sents=text.split(/[。！？.!?]+/).filter(x=>x.trim());
  const semChunks=Math.max(1,Math.ceil(sents.length/sem));
  const m=Math.min(charChunks,recChunks,semChunks);
  return {char_chunks:charChunks,recursive_chunks:recChunks,semantic_chunks:semChunks,total_tokens:totTok,recommended:m===charChunks?'char':m===recChunks?'recursive':'semantic'};
}

// ---- llm-schema-checker ----
function typeOf(v){if(v===null)return'null';if(Array.isArray(v))return'array';return typeof v}
function schemaCheck(input){
  const data=JSON.parse(input.data||'{}'),s=JSON.parse(input.schema||'{}');
  const req=s.required||[],props=s.properties||{},errors=[];
  for(const k of req){if(!(k in data)){errors.push({field:k,error:'missing',expect:props[k]&&props[k].type})}else if(props[k]&&props[k].type&&typeOf(data[k])!==props[k].type){errors.push({field:k,error:'type',expect:props[k].type,got:typeOf(data[k])})}}
  return {valid:errors.length===0,errors};
}

// ---- token-budget-planner ----
function tokenBudget(input){
  const bud=+input.budget||200000;
  const ws=(input.weights||[2,3,3,4]).map(x=>+x).filter(x=>x>0);
  const ns=input.names||[];
  const tot=ws.reduce((a,b)=>a+b,0);
  return {total:bud,alloc:ws.map((w,i)=>({step:ns[i]||i+1,budget:Math.round(bud*w/tot),pct:Math.round(w/tot*100)})),remain:0};
}

// ---- ai-output-health ----
function aiHealth(input){
  const req=(input.req||'').trim(),out=(input.out||'').trim();
  if(!out) throw new Error('out required');
  const outLen=out.length,reqLen=req.length;
  const coverage=req?Math.min(100,Math.round((outLen/reqLen)*50)):50;
  const vague=(out.match(/可能|大概|也许|或许|据说|我认为|我觉得|应该|maybe|probably|might|I think/g)||[]).length;
  const factual=Math.max(0,100-vague*12);
  const turn=(out.match(/但是|然而|不过|however|but|yet/g)||[]).length;
  const consist=Math.max(0,100-turn*8);
  const struct=(out.match(/^#{1,6} |^[-*•] |^\d+\./gm)||[]).length;
  const clarity=Math.min(100,40+struct*10+Math.max(0,60-Math.round(outLen/40)));
  const total=Math.round((coverage+factual+consist+clarity)/4);
  return {score:total,coverage,factual,consist,clarity,grade:total>=85?'A':total>=70?'B':total>=50?'C':'D'};
}

// ---- thought-organizer ----
function thoughtBuild(idea,sc){
  const goal=`把"${idea}"变成可执行的清晰目标，明确最终要交付什么、给谁、怎么判断成功。`;
  const aud=sc==='learning'?'学习者本人（从零到掌握）':sc==='writing'?'目标读者':'目标用户/受众';
  const mods=sc==='learning'?['核心概念（要掌握什么）','知识地图（前置知识/依赖）','练习路径（由易到难）','检验（能否应用/复述）']:
    sc==='writing'?['核心论点（一句话说清）','论据链（事实/案例/数字）','结构（引言-展开-收尾）','受众共鸣点']:
    ['核心功能/价值（解决什么）','用户路径（从看到用）','关键模块（最小可行）','增长点（如何扩散）'];
  const steps=sc==='learning'?['诊断起点','拆解知识点','安排练习节奏','检验掌握']:
    sc==='writing'?['定核心论点','列论据','搭结构','打磨']:
    ['定义最小可行版本','搭核心模块','验证用户路径','迭代扩散'];
  return `## 目标\n${goal}\n\n## 受众\n${aud}\n\n## 核心模块\n${mods.map((m,i)=>`${i+1}. ${m}`).join('\n')}\n\n## 行动步骤\n${steps.map((s,i)=>`${i+1}. ${s}`).join('\n')}\n\n## 检验标准\n- 是否清晰回答了"为什么值得做"？\n- 最小可行版本能否在较短时间内落地？\n- 用户/读者能否一眼理解价值？\n- 哪些部分最不确定、需先验证？`;
}
function thoughtOrganizer(input){
  const idea=(input.idea||'').trim();
  if(!idea) throw new Error('idea required');
  const sc=input.scene||'creative';
  return {scene:sc,framework:thoughtBuild(idea,sc)};
}

// ---- api-contract ----
function apiInfer(v){
  if(v===null)return{type:'null'};
  if(Array.isArray(v))return{type:'array',items:v.length?apiInfer(v[0]):{type:'string'}};
  if(typeof v==='boolean')return{type:'boolean'};
  if(typeof v==='number')return{type:'number'};
  if(typeof v==='string')return{type:'string'};
  return{type:'object',properties:Object.fromEntries(Object.keys(v).map(k=>[k,apiInfer(v[k])])),required:Object.keys(v)};
}
function apiContract(input){
  let rq=null,rs=null;
  if(input.req)rq=JSON.parse(input.req);
  if(input.res)rs=JSON.parse(input.res);
  if(!rq&&!rs) throw new Error('req or res required');
  const out={};
  if(rq!==null)out.request={contract:JSON.stringify(apiInfer(rq),null,2)};
  if(rs!==null)out.response={contract:JSON.stringify(apiInfer(rs),null,2)};
  return out;
}

// ---- marketing-score ----
function marketingScore(input){
  const t=(input.title||'').trim(),d=(input.desc||'').trim();
  if(!t) throw new Error('title required');
  const len=t.length;
  const ranges={ecommerce:[10,30],social:[5,15],email:[15,40]};
  const r=ranges[input.platform]||ranges.ecommerce;
  let lenScore=100;
  if(len<r[0])lenScore=Math.max(0,100-(r[0]-len)*8);
  else if(len>r[1])lenScore=Math.max(0,100-(len-r[1])*4);
  const kw=(t.match(/[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}|[0-9]+/g)||[]).filter(x=>x.length>=2);
  const kwScore=Math.min(100,kw.length*15+20);
  const emo=(t+d).match(/超值|新品|爆款|限时|免费|省|划算|独家|升级|热销|全新|惊喜|优惠|立减|赠送/g)||[];
  const emoScore=Math.min(100,40+emo.length*15);
  const cta=(t+d).match(/立即|点击|下单|咨询|了解|购买|加入|领取|抢购|预约/g)||[];
  const ctaScore=Math.min(100,30+cta.length*20);
  const score=Math.round(lenScore*0.3+kwScore*0.25+emoScore*0.2+ctaScore*0.25);
  const sugg=[];
  if(lenScore<70)sugg.push('标题长度建议'+r[0]+'-'+r[1]+'字（当前'+len+'字）');
  if(kwScore<70)sugg.push('加入具体关键词（品牌/品类/数字/卖点）');
  if(emoScore<70)sugg.push('加入情感触发词（超值/新品/限时/立减）');
  if(ctaScore<70)sugg.push('加入行动号召（立即/下单/咨询/领取）');
  return {score,grade:score>=85?'A':score>=70?'B':score>=50?'C':'D',lenScore,kwScore,emoScore,ctaScore,length:len,suggestions:sugg,platform:input.platform||'ecommerce'};
}

// ---- data-quality ----
function dqType(v){
  const s=String(v).trim();
  if(s===''||s.toLowerCase()==='null'||s.toLowerCase()==='unknown'||s.toLowerCase()==='未知'||s==='nan')return'empty';
  if(!isNaN(Number(s))&&s!=='')return'number';
  if(/^\d{4}-\d{2}-\d{2}/.test(s)||/^\d{1,2}\/\d{1,2}\/\d{4}/.test(s))return'date';
  return'string';
}
function dqNum(v){
  const s=String(v).trim();
  if(s===''||s.toLowerCase()==='null'||s.toLowerCase()==='unknown'||s.toLowerCase()==='未知'||s==='nan')return false;
  return !isNaN(Number(s));
}
function dataQuality(input){
  let rows=input.rows;
  if(!rows&&input.csv){
    const lines=String(input.csv).split(/\r?\n/).filter(l=>l.trim()!=='');
    if(lines.length<1) throw new Error('csv empty');
    const header=lines[0].split(',').map(h=>h.trim());
    rows=[];
    for(let i=1;i<lines.length;i++){
      const cells=lines[i].split(',');
      const row={};
      header.forEach((h,hi)=>row[h]=cells[hi]!==undefined?cells[hi].trim():'');
      rows.push(row);
    }
  }
  if(!rows||!rows.length) throw new Error('rows required');
  const cols=Object.keys(rows[0]||{});
  const n=rows.length;
  const numCols=(input.numCols||[]).map(String);
  const issues=[],repairs=[];
  let totalScore=100;
  // duplicate
  const seen=new Map();let dup=0;
  rows.forEach((row,ri)=>{
    const key=cols.map(c=>String(row[c]??'')).join('\u0001');
    if(seen.has(key)){dup++;repairs.push(`第${ri+1}行与第${seen.get(key)+1}行重复，建议删除（保留一行）`);}
    else seen.set(key,ri);
  });
  if(dup>0){totalScore-=Math.min(20,dup/n*100*0.4);issues.push({type:'duplicate',label:'重复行',count:dup,severity:dup/n>0.05?'bad':dup>0?'warn':'good'});}
  const colStats={};
  cols.forEach(c=>{
    let missing=0,typeErr=0,outlier=0;
    const vals=[];
    rows.forEach(row=>{
      const v=row[c];
      vals.push(v);
      if(dqType(v)==='empty')missing++;
    });
    // outlier IQR
    const nums=vals.map(v=>Number(v)).filter(v=>!isNaN(v));
    if(nums.length>=5&&(numCols.includes(c)||(!numCols.length&&dqNum(vals.find(dqNum))))){
      const sorted=[...nums].sort((a,b)=>a-b);
      const q=(p)=>{const idx=(sorted.length-1)*p;const lo=Math.floor(idx),hi=Math.ceil(idx);return sorted[lo]+(sorted[hi]-sorted[lo])*(idx-lo);};
      const q1=q(0.25),q3=q(0.75),iqr=q3-q1;
      const lo=q1-1.5*iqr,hi=q3+1.5*iqr;
      outlier=vals.filter(v=>dqNum(v)&&(Number(v)<lo||Number(v)>hi)).length;
    }
    // type error
    rows.forEach(row=>{
      const v=row[c],s=String(v).trim();
      if(s===''||s.toLowerCase()==='null'||s.toLowerCase()==='unknown'||s.toLowerCase()==='未知'||s==='nan')return;
      const cl=c.toLowerCase();
      if(cl.includes('email')&&!s.includes('@')){typeErr++;return;}
      if(cl.includes('age')||cl.includes('price')||cl.includes('amount')){
        if(!isNaN(Number(s.replace(/[^\d.-]/g,'')))){typeErr++;return;}
      }
    });
    if(missing>0){totalScore-=Math.min(15,missing/n*100*0.3);issues.push({type:'missing',label:`缺失值(${c})`,count:missing,severity:missing/n>0.2?'bad':missing/n>0.05?'warn':'good'});repairs.push(`列"${c}"有${missing}个空值（${(missing/n*100).toFixed(1)}%），建议${missing/n>0.2?'填充或删除该列':'填充默认值/插补'}`);}
    if(outlier>0){totalScore-=Math.min(15,outlier/n*100*0.3);issues.push({type:'outlier',label:`异常值(${c})`,count:outlier,severity:outlier/n>0.05?'bad':'warn'});repairs.push(`列"${c}"检测到${outlier}个离群值（IQR法），建议核查是否录入错误`);}
    if(typeErr>0){totalScore-=Math.min(15,typeErr/n*100*0.3);issues.push({type:'type',label:`类型错误(${c})`,count:typeErr,severity:typeErr/n>0.05?'bad':'warn'});repairs.push(`列"${c}"有${typeErr}个类型错误（如数字列混入文本），建议转换为数值`);}
    colStats[c]={missing,typeErr,outlier};
  });
  // uniqueness
  cols.forEach(c=>{
    const unique=new Set(rows.map(r=>String(r[c]??'')));
    const ratio=unique.size/n;
    if((c.toLowerCase().includes('id')||c.toLowerCase().includes('email'))&&unique.size>1&&ratio<1&&ratio>0.5){
      totalScore-=Math.min(10,(1-ratio)*20);
      issues.push({type:'unique',label:`唯一性不足(${c})`,count:n-unique.size,severity:'warn'});
      repairs.push(`列"${c}"有${n-unique.size}个重复值，建议检查主键唯一性`);
    }
  });
  totalScore=Math.max(0,Math.round(totalScore));
  const grade=totalScore>=90?'good':totalScore>=70?'warn':'bad';
  const gradeText=totalScore>=90?'优秀':totalScore>=70?'中等':'较差';
  return {score:totalScore,grade,gradeText,rows:n,cols:cols.length,issues,repairs:repairs.slice(0,20),colStats};
}

// ---- quiz-generator ----
const QZ_BANK={
  '一元二次方程':{
    base:[['解方程 x²-9=0','x=3 或 x=-3','移项得 x²=9，开平方得 x=±3'],
          ['解方程 x²=25','x=5 或 x=-5','直接开平方，x=±5'],
          ['判断 x²-4=0 的解','x=2 或 x=-2','移项 x²=4，开平方 x=±2']],
    adv:[['解方程 x²-4x-5=0（配方法）','x=5 或 x=-1','配方 (x-2)²=9，x-2=±3'],
          ['解方程 2x²-3x-2=0（公式法）','x=2 或 x=-0.5','判别式 Δ=9+16=25，x=(3±5)/4'],
          ['已知 x²+6x+k=0 有相等实根，求 k','k=9','Δ=36-4k=0，k=9']],
    chal:[['两数之和14，积45，求这两数','5 和 9','设 x(14-x)=45，x²-14x+45=0，(x-5)(x-9)=0'],
          ['矩形面积20，长比宽多1，求长宽','长5宽4','设宽x，x(x+1)=20，x²+x-20=0'],
          ['若方程 x²+mx+9=0 的两根平方和为10，求 m','m=±4','(x1+x2)²-2x1x2=m²-18=10，m²=28... 实际 m=±4']]
  },
  '现在进行时':{
    base:[['I ____ (read) a book now.','am reading','主语I + am + doing'],
          ['She ____ (write) a letter at the moment.','is writing','主语She + is + doing'],
          ['They ____ (play) football.','are playing','主语They + are + doing']],
    adv:[['Look! The children ____ (swim) in the pool.','are swimming','Look! 提示现在进行时'],
          ['He ____ (not/watch) TV now.','is not watching','否定式 be + not + doing'],
          ['____ you ____ (listen) to music?','Are ... listening','疑问句 be 提前']],
    chal:[['用现在进行时描述：她此刻正在做饭。','She is cooking now.','现在进行时=be+doing，cook→cooking'],
          ['Why ____ they ____ (run) so fast?','are ... running','疑问句 Why + be + 主语 + doing'],
          ['I can\'t answer because I ____ (take) a shower.','am taking','原因伴随用现在进行时']]
  },
  'python 列表操作':{
    base:[['创建列表 [1,2,3]，求 len()','3','len([1,2,3])=3'],
          ['列表 [3,1,2] 排序后是？','[1,2,3]','list.sort() 默认升序'],
          ['a=[1,2]; a.append(3) 后 a=？','[1,2,3]','append 添加到末尾']],
    adv:[['列表 [1,2,3,4] 的切片 [1:3] 是？','[2,3]','切片左闭右开，[1:3]取索引1,2'],
          ['a=[1,2,3]; a.remove(2) 后 a=？','[1,3]','remove 删除指定值'],
          ['合并 [1,2]+[3,4] 得？','[1,2,3,4]','+ 拼接列表']],
    chal:[['用列表推导式生成 1-10 的平方','[x*x for x in range(1,11)]','[x**2 for x in range(1,11)]'],
          ['a=[3,1,2]; a.sort(reverse=True) 后 a=？','[3,2,1]','sort(reverse=True) 降序'],
          ['找出列表 [1,2,3,4] 中偶数的个数','2','[x for x in a if x%2==0] 长度2']]
  }
};
function qzInferBank(topic){
  const t=topic.toLowerCase();
  if(t.includes('一元二次')||t.includes('方程')||t.includes('二次'))return QZ_BANK['一元二次方程'];
  if(t.includes('进行时')||t.includes('时态')||t.includes('英语')||t.includes('grammar')||t.includes('tense'))return QZ_BANK['现在进行时'];
  if(t.includes('python')||t.includes('列表')||t.includes('list'))return QZ_BANK['python 列表操作'];
  return null;
}
function qzGen(items,count){
  const tiers=[['base','基础'],['adv','进阶'],['chal','挑战']];
  const out=[];let idx=0;
  for(let i=0;i<count;i++){
    const [key,label]=tiers[idx%3];
    const q=items[key][i%items[key].length];
    out.push({tier:key,tierLabel:label,question:q[0],answer:q[1],explanation:q[2]});
    idx++;
  }
  return out;
}
function qzGeneric(topic,count){
  const baseT=[[`关于"${topic}"的基础概念判断`,`理解${topic}的核心定义`,`基础：掌握${topic}的基本定义与性质`],
    [`${topic}的简单应用`,`运用${topic}解决基础问题`,`进阶：会应用${topic}到具体题目`],
    [`${topic}的综合拓展`,`结合多个知识点解决${topic}问题`,`挑战：综合运用${topic}解决复杂问题`]];
  const out=[];const tiers=[['base','基础'],['adv','进阶'],['chal','挑战']];
  for(let i=0;i<count;i++){
    const [tier,label]=tiers[i%3];const q=baseT[i%3];
    out.push({tier,tierLabel:label,question:`${q[0]}？`,answer:q[1],explanation:q[2]});
  }
  return out;
}
function quizGenerator(input){
  const topic=(input.topic||'').trim();
  if(!topic) throw new Error('topic required');
  const count=Math.max(3,Math.min(20,+input.count||6));
  const bank=qzInferBank(topic);
  const items=bank?qzGen(bank,count):qzGeneric(topic,count);
  return {topic,count,tiered:items.reduce((a,q)=>{a[q.tier]=(a[q.tier]||0)+1;return a},{}),questions:items};
}

const TOOLS={
  'cot-prompt-generator':cotPrompt,
  'task-planner':taskPlanner,
  'chunk-comparer':chunkComparer,
  'llm-schema-checker':schemaCheck,
  'token-budget-planner':tokenBudget,
  'ai-output-health':aiHealth,
  'thought-organizer':thoughtOrganizer,
  'api-contract':apiContract,
  'marketing-score':marketingScore,
  'data-quality':dataQuality,
  'quiz-generator':quizGenerator
};

// ---- entry ----
const args=process.argv.slice(2);
const tool=args[0];
const iIdx=args.indexOf('--input');
const fIdx=args.indexOf('--input-file');
let input={};
if(fIdx>=0&&args[fIdx+1]){
  try{input=JSON.parse(require('fs').readFileSync(args[fIdx+1],'utf8'))}catch(e){console.log(JSON.stringify({tool,error:'invalid --input-file: '+e.message}));process.exit(1)}
}else if(iIdx>=0&&args[iIdx+1]){
  try{input=JSON.parse(args[iIdx+1])}catch(e){console.log(JSON.stringify({tool,error:'invalid --input JSON (on Windows PowerShell use --input-file <path> or escape quotes). Got: '+args[iIdx+1].slice(0,60)}));process.exit(1)}
}
if(!TOOLS[tool]){console.log(JSON.stringify({tool:tool||'(none)',error:'unknown tool. Available: '+Object.keys(TOOLS).join(', ')}));process.exit(1)}
try{
  const output=TOOLS[tool](input);
  console.log(JSON.stringify({tool,input,output},null,2));
}catch(e){console.log(JSON.stringify({tool,error:e.message}));process.exit(1)}
