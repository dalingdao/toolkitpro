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

const TOOLS={
  'cot-prompt-generator':cotPrompt,
  'task-planner':taskPlanner,
  'chunk-comparer':chunkComparer,
  'llm-schema-checker':schemaCheck,
  'token-budget-planner':tokenBudget,
  'ai-output-health':aiHealth
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
