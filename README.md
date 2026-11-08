# ToolkitPro

**200+ 免费在线工具 · 纯前端 · GitHub Pages · Agent-Ready**

![GitHub stars](https://img.shields.io/github/stars/dalingdao/toolkitpro)
![tools](https://img.shields.io/badge/tools-200-blue)
![Agent-Ready](https://img.shields.io/badge/Agent-Ready-purple)
![CLI](https://img.shields.io/badge/CLI-JS%2BPython-green)

> **访问：** <https://dalingdao.github.io/toolkitpro/>

## 这是什么

200 个纯前端在线工具，**全部免费、无需注册、无需后端、秒开**。

不是简单复制已有工具——每个工具针对一个具体**痛点**做**差异化设计**：更快、更准、更贴合真实场景，并内置 **AI Agent 可直接调用的 JSON 接口**。

## 工具亮点

- **纯前端**：秒开、无追踪、数据不离开浏览器
- **Agent-Ready**：每个工具支持 `?tool=xxx&input=yyy&format=json`，返回结构化 JSON，AI Agent 可直接调用
- **本地优先**：待办/习惯/日记等状态数据保存在浏览器本地
- **分类覆盖**：财务计算、健康、数据转换、文本处理、图片、开发者工具等

## 原创差异化工具（Agent-Ready + CLI）

这些不是复制品——针对具体**痛点**原创设计，网页/Agent/CLI 三接口：

| 工具 | 解决什么痛点 | 能改变什么 |
|---|---|---|
| **CoT Prompt 生成器** | 普通人不会写 AI 提示词 | 一键生成思维链提示词，AI 输出更可靠 |
| **Agent 任务规划器** | 模糊目标难执行 | 拆成可执行子任务+token 预算 |
| **RAG 分块对比** | 选错分块策略 | 三策略对比，检索更准 |
| **LLM Schema 校验** | AI 输出不可信 | JSON Schema 校验，防幻觉进生产 |
| **Token 预算分配** | 多步任务超支 | 步骤级预算分配 |
| **AI 输出质量体检** | AI 内容质量难判断 | 事实性/一致性/完整性/清晰度评分 |
| **思维结构化器** | 想法混乱难落地 | 模糊想法→可执行框架 |
| **API 契约生成器** | 手写 Schema 易错 | 示例→JSON Schema 草案+类型推断 |
| **营销文案评分器** | 文案吸引力难判断 | 长度/关键词/情感/CTA 量化+改进建议 |
| **数据质量体检器** | 数据分析师难判断数据能否用 | 缺失/重复/异常/类型错误检测+评分+修复建议 |
| **分层练习生成器** | 教师备课出题慢、难分层 | 知识点→基础/进阶/挑战三层题目+答案+解析 |
| **需求优先级矩阵** | 产品经理排需求凭直觉 | 价值/成本/风险/依赖四维量化→优先级排序+P0-P3分级 |
| **FAQ 智能整理器** | 客服问答零散难整理 | 自动归类+合并重复问题+可搜索FAQ文档 |
| **多语言一致性检查器** | i18n 键不同步/占位符漏翻 | 缺失/多余/占位符/长度异常→一致性报告 |
| **测试用例生成器** | QA 用例覆盖不全/漏边界 | 等价类+边界值+异常场景用例+优先级 |

每个支持：`?tool=xxx&input=yyy&format=json`（网页 JSON）+ `node cli.js` / `python cli.py`（命令行）。

## Agent 接口

```
https://dalingdao.github.io/toolkitpro/{tool}/?tool={tool}&input={input}&format=json
```

返回 `{ "tool": "...", "input": "...", "output": {...} }`。

示例：`https://dalingdao.github.io/toolkitpro/bmi-calculator/?tool=bmi-calculator&input={"weight":70,"height":1.75}&format=json`

## CLI 用法

每个原创工具也可**命令行调用**（计算逻辑与页面完全一致，返回 JSON）。支持 **JS 与 Python** 双实现：

```bash
# Node.js
node cli.js cot-prompt-generator --input '{"task":"帮我写一篇产品介绍","scenario":"writing"}'

# Python
python cli.py cot-prompt-generator --input '{"task":"帮我写一篇产品介绍","scenario":"writing"}'
```

跨平台稳定（Windows/CI）用文件输入：

```bash
node cli.js task-planner --input-file input.json
python cli.py task-planner --input-file input.json
```

输出：`{ "tool": "...", "input": {...}, "output": {...} }`。

可用工具：`cot-prompt-generator`、`task-planner`、`chunk-comparer`、`llm-schema-checker`、`token-budget-planner`、`ai-output-health`、`thought-organizer`、`api-contract`、`marketing-score`、`data-quality`、`quiz-generator`、`priority-matrix`、`faq-generator`、`i18n-checker`、`test-case-gen`。

```bash
node cli.js        # 列出全部可用工具（cli.py 同理）
```

## 工具分类

- **财务计算器**：贷款、投资、复利、退休、税费等
- **健康工具**：BMI、卡路里、血压、孕期、睡眠等
- **数据转换**：JSON/CSV/YAML/TOML、Base64、哈希、时间戳等
- **文本工具**：字数统计、去重、大小写、格式化等
- **图片工具**：格式转换、压缩、水印、占位图等
- **开发者工具**：正则测试、JWT 解码、User-Agent 解析、URL 解析等

## 为什么与别的工具不同

- **统一 Agent 接口**：多数在线工具是给人用的；这些工具同时是 **Agent 的可调用能力**（结构化输入/输出）。
- **零依赖纯前端**：单页即开即用，部署在 GitHub Pages，无服务器成本。
- **痛点导向**：每个工具按"解决什么痛点、能改变什么、比同类优在哪"设计。

## Star

如果这些工具对你有用，欢迎点 **Star** 支持这个仓库。

---

*纯前端开源工具集，部署于 GitHub Pages。*
