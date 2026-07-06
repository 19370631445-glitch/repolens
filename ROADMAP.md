# RepoLens 开发路线图

> 路线图性质：方向性计划，不是不可变承诺  
> v0.1 目标周期：2–3 周  
> 当前优先级：先验证 CLI 生成的 `PROJECT_MAP.md` 是否真正有用

## 1. 路线图原则

- 先完成一个可靠的 end-to-end workflow，再扩展语言和 provider；
- 每个版本都必须可以独立安装、运行和演示；
- 优先改善报告质量、可解释性和安全性；
- 不以功能数量换取复杂度；
- 根据真实 GitHub users 的 feedback 调整 v0.2 和 v1.0；
- Future Features 不应提前进入 v0.1。

## 2. Version 0.1 — MVP

### 2.1 版本目标

用户可以安装 RepoLens，输入一个公开 GitHub repository URL，并得到结构清晰、带证据和限制说明的 `PROJECT_MAP.md`。

### 2.2 包含范围

- Python 3.11+ CLI；
- `repolens analyze <github-url>`；
- GitHub public repository；
- default branch shallow clone；
- 安全文件遍历和排除规则；
- directory tree 和语言统计；
- manifest/config 驱动的 technology stack detection；
- 可解释的重要文件 ranking；
- JavaScript/TypeScript 和 Python 的轻量 import 与 module relationship 提取；
- 其他语言的通用 directory/file-level analysis；
- 单一 OpenAI provider；
- 有资源上限的 hierarchical LLM summarization；
- 包含“推断的基础 data flow”的固定结构 `PROJECT_MAP.md`；
- 进度提示、基础统计和可操作错误；
- unit、integration、snapshot tests；
- 面向初学者的扁平 module layout；
- open-source release 必需文档和示例。

### 2.3 明确排除

- Web UI；
- authentication；
- database；
- private repository；
- local repository input；
- branch/tag/commit 选择；
- full AST engine；
- autonomous agent exploration；
- repository code execution；
- multi-provider support；
- caching 和 incremental analysis；
- IDE extension；
- GitHub App 或用于 repository analysis 的 GitHub Action integration；用于本项目自身质量检查的 GitHub Actions workflow 可作为可选 release polish。

### 2.4 v0.1 Release Gate

- 从干净环境可按文档完成安装；
- 至少覆盖多个不同技术栈的 fixture repositories；
- Mock LLM 的 end-to-end tests 稳定通过；
- 输出包含所有 required sections；
- 报告能引用关键 evidence paths 并标记 inference；
- 常见失败场景均有可操作错误；
- 安全检查确认不会执行目标代码或跟随 symlink；
- 文档明确披露 remote LLM、费用、secret 和 hallucination 风险；
- package 可以构建并安装；
- `README.md` 包含 Quick Start、安装说明和可复制的 usage example；
- repository 包含 `LICENSE` 和至少一份 sample `PROJECT_MAP.md`；
- lint、test 和 package build 可通过本地命令完成。

### 2.5 可选 Release Polish

以下内容有价值，但不阻塞 v0.1：

- `CONTRIBUTING.md`；
- `CODE_OF_CONDUCT.md`；
- bug、analysis quality 和 feature request issue templates；
- 完整 GitHub Actions workflows；
- 更完整的 maintainer 和 contributor workflow。

## 3. Version 0.2 — Quality and Extensibility

v0.2 在 v0.1 获得真实反馈后规划，重点是质量和重复使用体验，而不是立刻增加 Web UI。

### 3.1 候选改进

- 支持 local repository path；
- 支持指定 branch、tag 或 commit；
- 增加 Anthropic 或 Ollama provider；
- 缓存 deterministic analysis 和 LLM summaries；
- 生成 machine-readable JSON 中间结果；
- 更准确的 Python、JavaScript/TypeScript import extraction；
- monorepo package detection 的初步支持；
- 可配置的 analysis limits；
- 更清晰的 token/cost preview；
- 对被忽略内容提供更完整的审计摘要；
- 改善 partial report 和 provider failure recovery；
- 建立公开的 example report gallery。

### 3.2 v0.2 进入条件

只有在 v0.1 稳定后才开始：

- 核心 pipeline 的 bug 和安全问题已处理；
- 已收集真实用户的 analysis quality feedback；
- 已确认最常见的第二 provider 或 local model 需求；
- 当前 interfaces 足以扩展，不需要大规模重写。

### 3.3 v0.2 不默认承诺

上述项目是候选 backlog。版本规划时应根据使用数据只选择少量高价值项目，避免把 v0.2 变成“大而全”的版本。

## 4. Version 1.0 — Stable Repository Understanding Platform

### 4.1 愿景

RepoLens 1.0 成为可信、可扩展的 open-source repository understanding 基础工具：既能被开发者直接作为 CLI 使用，也能被其他工具通过稳定接口集成。

### 4.2 可能能力

- 稳定的 CLI 和 machine-readable output contract；
- 多个成熟的 LLM providers，包括可选 local model；
- 可扩展 language analyzer interface；
- 大型 repository 和 monorepo 的选择性分析；
- report diff，解释架构在 commits 之间的变化；
- GitHub Action 或 CI integration；
- plugin system；
- 更丰富但仍可追溯的 module/data flow；
- 可选 Web interface，复用同一 analysis core；
- 完整的隐私、安全和 provider 配置文档；
- 稳定 release process 和活跃 contributor workflow。

### 4.3 1.0 稳定性标准

- CLI 参数和 report schema 有兼容性策略；
- provider 和 analyzer extension interfaces 有文档与示例；
- 核心 pipeline 在支持矩阵内有可靠测试；
- 明确支持的 repository 规模和语言范围；
- 有迁移指南、changelog 和 security policy；
- 社区可以在不理解全部内部实现的情况下贡献 analyzer 或 provider。

## 5. Development Milestones

### Milestone 0 — 产品与架构冻结

预计：1–2 天

交付：

- `PRD.md`；
- `TECH_DESIGN.md`；
- `ROADMAP.md`；
- 确认 v0.1 非目标；
- 选择 license 和 package name；
- 建立少量代表性 fixture repository 清单。

完成标准：

- 产品范围与 2–3 周周期一致；
- 没有 Web、database、authentication、full AST 或 agent loop；
- 所有核心 component 有清晰责任边界。

### Milestone 1 — CLI Skeleton and Repository Acquisition

预计：2–3 天

交付：

- Python package 和 CLI entry point；
- 建立 `cli.py`、`config.py`、`errors.py`、`git_source.py`、`scanner.py`、`analyzer.py`、`llm.py`、`report.py` 的扁平初始结构；
- typed configuration；
- Git 和 API key 环境检查；
- GitHub URL validation；
- shallow clone 与 temporary workspace cleanup；
- 基础错误模型和测试。

完成标准：

- 能安全获取公开 repository；
- clone 失败和环境缺失时提示清晰；
- 无论成功或失败都不会遗留未管理的临时目录。

### Milestone 2 — Scanner and Filters

预计：2 天

交付：

- 安全 scanner；
- ignore、binary、generated 和 secret-like filters；
- directory tree 和语言统计；
- resource limits 和 unit tests。

完成标准：

- 对 fixtures 产生 deterministic file inventory；
- symlink 和 oversized repository 场景受到限制；
- 不执行任何 repository code；
- 跳过和截断原因可以被后续报告引用。

### Milestone 3 — Technology Detection and Importance Ranking

预计：2 天

交付：

- manifest/config 驱动的 technology detection；
- JavaScript/TypeScript 和 Python 优先规则；
- 其他语言的通用 file-level detection；
- 可解释的 importance ranking；
- evidence paths 和 unit tests。

完成标准：

- 重要技术栈结论带 evidence path；
- 相同输入得到稳定的文件排序；
- 每个高排名文件可以说明入选原因；
- 不引入 AST engine 或 language server。

### Milestone 4 — Lightweight Relationship Extraction

预计：1–2 天

交付：

- JavaScript/TypeScript 和 Python 常见 import pattern；
- module-level relationship clues；
- evidence 和 confidence 标记；
- “推断的基础 data flow”所需结构化线索；
- relationship tests。

完成标准：

- 关系可以定位到 repository-relative paths；
- 推断关系不会被标记为确定事实；
- 其他语言只进行通用目录和文件级分析；
- dynamic import 和复杂 framework behavior 明确不在范围内。

### Milestone 5 — LLM Summarization Pipeline

预计：3–4 天

交付：

- provider interface 和 OpenAI implementation；
- typed prompts 和 responses；
- context builder 和 batching；
- file、module、project 三层 summary；
- timeout、retry 和错误映射；
- Mock LLM integration tests。

完成标准：

- 默认测试不需要真实 API；
- context 和调用次数有硬上限；
- repository prompt injection 不能改变 pipeline 控制流；
- LLM 无效输出能够被 validation 捕获。

### Milestone 6 — PROJECT_MAP.md Report

预计：2–3 天

交付：

- 固定 Markdown template；
- required sections；
- evidence 和 inference 标记；
- 明确标记“推断的基础 data flow”；
- limitations 与 analysis metadata；
- 原子写入；
- snapshot tests。

完成标准：

- 每个成功运行都生成完整结构；
- 报告可直接在 GitHub Markdown renderer 中阅读；
- 输出引用使用 repository-relative paths；
- 部分覆盖和跳过内容对用户透明。

### Milestone 7 — Open-source Release Readiness

预计：2–3 天

必需交付：

- `README.md`，包含安装说明、Quick Start 和可复制的 usage example；
- `LICENSE`；
- sample `PROJECT_MAP.md`；
- 可在本地运行的 lint、test 和 package build commands；
- release checklist 和 changelog；
- 安全、隐私、费用和准确性说明。

完成标准：

- 初学者能按照 README 独立完成首次运行；
- 在干净环境中 package 安装成功；
- 本地质量检查稳定通过；
- sample `PROJECT_MAP.md` 可以从文档中的公开 repository 示例复现；
- known limitations 清晰，不夸大分析能力。

可选 release polish：

- `CONTRIBUTING.md`；
- `CODE_OF_CONDUCT.md`；
- issue templates；
- 完整 GitHub Actions workflows。

### Milestone 8 — v0.1 Release and Feedback

预计：1 天发布，随后持续收集 feedback

交付：

- `v0.1.0` release；
- example `PROJECT_MAP.md`；
- 首批 feedback issues；
- v0.2 backlog 排序。

完成标准：

- release artifact 可安装；
- 示例可复现；
- 必需 release materials 完整；
- 如已增加 issue templates 或 labels，应区分 bug、analysis quality、provider 和 feature request。

## 6. 建议的 3 周节奏

### Week 1

- 完成 Milestone 0；
- 完成 CLI、配置、GitHub Source；
- 完成 Milestone 2 的 scanner 和 filters；
- 建立 fixtures 和核心 unit tests。

### Week 2

- 完成 Milestone 3 和 4；
- 完成 Context Builder；
- 接入 OpenAI provider；
- 完成 Mock LLM 的 end-to-end pipeline。

### Week 3

- 完成 report template 和 snapshot tests；
- 处理安全边界和失败体验；
- 编写必需的 open-source 文档与 sample `PROJECT_MAP.md`；
- 完成 release check，发布 `v0.1.0`。

如果时间不足，优先保证报告结构、证据引用、安全过滤和错误处理；应删除次要 CLI options、较弱的 relationship heuristics 或可选 release polish，而不是加入额外基础设施。

## 7. Backlog Prioritization

后续 feature 使用以下顺序评估：

1. 是否明显提升 `PROJECT_MAP.md` 的准确性或可用性；
2. 是否解决多个真实用户反复遇到的问题；
3. 是否能复用现有 pipeline，而不引入长期 server infrastructure；
4. 是否可以被测试并保持 deterministic boundary；
5. 是否符合 open-source contributor 可以理解和维护的复杂度。

以下信号不足以单独推动 feature：

- “看起来更像完整产品”；
- 只为演示效果增加 UI；
- 尚无用户需求的通用 abstraction；
- 依赖 autonomous agent 才能工作的不稳定流程；
- 为未来可能需要的规模提前引入 database 或 distributed system。

## 8. 初学者与 Codex 协作建议

- 每次只实现一个 Milestone 中的一个可验证目标；
- 让 Codex 在修改前引用本 PRD 和 Technical Design；
- 要求每个功能同时提供 tests 和清晰错误信息；
- 每完成一个阶段就运行完整 test suite；
- 不接受未解释的新 framework、database 或 background service；
- 当实现建议超出 v0.1 时，先记录到 backlog，不立即编码；
- 使用小型 commits，让每个 commit 都可以说明“解决了什么问题”；
- release 前对真实公开 repository 做少量手动验证，但不要把联网测试放入默认 CI。

## 9. 版本决策检查表

任何新增需求进入 v0.1 前，都应回答：

- 它是否是生成有效 `PROJECT_MAP.md` 的必要条件？
- 不做它，v0.1 是否仍可被真实用户使用？
- 它能否在剩余周期内实现并测试？
- 它是否引入 Web UI、authentication、database、full AST 或 autonomous agent？
- 它是否增加新的隐私或安全风险？

若不是必要条件，默认推迟到 v0.2 backlog。
