# RepoLens 产品需求文档

> 文档状态：v0.1 MVP 已批准  
> 面向版本：RepoLens 0.1  
> 产品形态：Open-source Python CLI  
> 核心产物：`PROJECT_MAP.md`

## 1. 产品概述

RepoLens 是一个由 AI 辅助的代码仓库理解工具。用户提供公开的 GitHub repository URL，RepoLens 在本地完成轻量级静态分析，并调用 LLM 将分析结果整理为易于阅读的 `PROJECT_MAP.md`。

v0.1 优先分析 JavaScript/TypeScript 和 Python 项目。对于其他语言，RepoLens 只提供通用的目录、文件和配置层分析，不承诺语言专用的模块关系提取。v0.1 的目标不是完整理解每一行代码，而是在较短时间内为开发者建立一张可信、可追溯的项目地图，帮助其决定下一步应该阅读哪些目录、文件和模块。

## 2. 问题陈述

开发者经常需要接手不熟悉的代码仓库，例如：

- 新公司的内部项目；
- 准备贡献的 open-source repository；
- 缺少文档的 legacy codebase；
- 需要快速评估的技术样例或依赖项目。

传统方式需要手动浏览大量目录、配置文件和源代码。仓库越大，建立整体认知所需的时间越长。现有通用 AI 对话工具还常见以下问题：

- 用户需要手动选择并上传上下文；
- 容易忽略项目结构和依赖配置；
- 输出缺少统一格式，难以保存或分享；
- 可能把推测表达成确定事实；
- 大型仓库容易超过 LLM context window。

RepoLens 通过自动收集仓库结构、识别技术栈、筛选重要文件、分层压缩上下文并生成固定格式报告，降低理解陌生仓库的第一步成本。

## 3. 目标用户

### 3.1 主要用户

- 刚加入项目、需要快速 onboarding 的开发者；
- 想了解或贡献 GitHub 开源项目的开发者；
- 使用 Codex 等 AI coding tools 的初学者；
- 需要快速评估代码仓库的独立开发者。

### 3.2 次要用户

- 需要为项目补充架构说明的 open-source maintainer；
- 需要初步了解 inherited codebase 的技术负责人；
- 学习真实项目组织方式的编程学习者。

### 3.3 v0.1 使用前提

用户应具备：

- 基本的 terminal 使用能力；
- 本地已安装 Python 和 Git；
- 可访问 GitHub；
- 自行提供受支持 LLM provider 的 API key；
- 理解 AI 生成内容可能存在错误，需要结合源代码验证。

## 4. 用户故事

### 4.1 核心用户故事

- 作为新加入项目的开发者，我希望输入一个 GitHub URL 后得到项目概览，以便快速理解项目用途。
- 作为初学者，我希望看到技术栈及其判断依据，以便知道应该先学习哪些工具和框架。
- 作为开源贡献者，我希望知道关键目录和重要文件，以便从正确的入口开始阅读。
- 作为维护者，我希望看到主要模块之间的关系，以便检查当前文档是否遗漏关键结构。
- 作为开发者，我希望获得明确标记为推断的基础 data flow 说明，以便了解输入可能如何经过主要模块并产生输出，同时不会把推断误认为事实。
- 作为用户，我希望报告保存为 Markdown，以便在本地阅读、版本控制和分享。

### 4.2 可靠性用户故事

- 作为用户，当 URL 无效、Git 不可用或 API key 缺失时，我希望看到明确且可操作的错误提示。
- 作为用户，我希望 RepoLens 不执行目标仓库中的任何代码，以降低分析陌生仓库的风险。
- 作为用户，我希望报告区分“静态分析事实”和“AI 推断”，避免把推测误认为事实。
- 作为用户，我希望能够看到被跳过的内容和分析限制，从而正确理解报告覆盖范围。

## 5. 产品目标

### 5.1 v0.1 目标

1. 通过一个 CLI command 完成公开 GitHub repository 的分析。
2. 自动生成结构稳定、可读的 `PROJECT_MAP.md`。
3. 对常见小型和中型仓库提供有用的第一层项目认知。
4. 控制 LLM context、成本和延迟，避免直接把整个仓库发送给模型。
5. 提供适合 GitHub open-source release 的安装、使用和贡献基础。
6. 让初学者能够借助清晰文档和错误提示完成首次分析。

### 5.2 非目标

v0.1 不追求：

- 证明对仓库的完整或形式化理解；
- 生成精确到函数级别的 call graph；
- 替代人工 code review、security audit 或架构评审；
- 对任意规模和任意语言仓库提供同等深度；
- 在 JavaScript/TypeScript 和 Python 之外提供语言专用的深度分析；
- 自动修改目标仓库。

## 6. MVP 范围

### 6.1 输入

- 一个公开 GitHub repository 的 HTTPS URL；
- 可选的本地输出文件路径；
- 必需的 LLM API 配置；
- 少量用于控制模型和分析规模的 CLI options。

v0.1 只分析 repository default branch 的最新状态，不提供 branch、tag 或 commit 选择能力。

### 6.2 Repository 获取

- 验证输入是否为受支持的 GitHub repository URL；
- 使用 shallow clone 获取 default branch；
- 在临时工作目录中分析；
- 分析完成或失败后清理临时内容；
- clone 失败时输出可操作的错误信息。

### 6.3 轻量级静态分析

RepoLens 应收集：

- 目录树和文件类型分布；
- 主要 programming languages；
- package manifest、lockfile、build、test、CI 和 deployment 配置；
- 常见入口文件和文档文件；
- import、配置引用和命名约定所暗示的模块关系；
- 适合提交给 LLM 的关键文件片段。

语言支持分为两层：

- **优先语言**：JavaScript、TypeScript 和 Python。v0.1 可为这些语言提供基于常见 import pattern、entry point 和配置文件的轻量关系分析；
- **其他语言**：只提供通用 directory/file-level analysis，包括目录树、文件类型、常见 manifest/config、重要文件筛选和 LLM 文件摘要。

RepoLens 不构建完整 AST。即使对于优先语言，也不保证完整解析 dynamic import、runtime dependency injection 或所有 framework conventions。无法可靠确认的关系必须标记为推断。

### 6.4 文件筛选

默认跳过：

- 二进制和媒体文件；
- dependency/vendor 目录；
- build artifacts、cache 和 generated files；
- minified files；
- 超过安全大小阈值的单个文件；
- `.gitignore` 排除的文件；
- 常见 secret、credential 和本地环境文件。

扫描器应设置文件数量、单文件大小和总文本量上限。达到上限时继续生成报告，但必须在报告中说明覆盖限制。

### 6.5 重要性排序

文件优先级由可解释的规则产生，主要考虑：

- 是否为 README、manifest、lockfile 或主要配置文件；
- 是否为常见 application entry point；
- 是否位于核心 source directory；
- 是否被多个文件引用；
- 文件名和路径是否表达明确的架构职责；
- 文件大小是否处于适合分析的范围。

v0.1 不使用 autonomous agent 自行决定并反复探索文件。

### 6.6 LLM 项目理解

LLM 处理采用分层总结：

1. 将确定性 static analysis 结果整理为结构化上下文；
2. 对选中的关键文件分批生成摘要；
3. 合并为模块级理解；
4. 生成最终项目报告；
5. 对结构化输出进行基本 validation。

Repository 内容一律视为不可信数据，不能作为 RepoLens 的系统指令。

### 6.7 输出

默认在当前目录生成 `PROJECT_MAP.md`，至少包含：

1. 项目概览；
2. 技术栈分析及判断依据；
3. 目录结构说明；
4. 重要文件说明；
5. 核心模块关系；
6. 推断的基础 data flow；
7. 推荐阅读顺序；
8. 分析范围、跳过内容和已知限制；
9. 生成时间、目标 repository 和 commit SHA 等元数据。

报告中的重要判断应尽量附带相对文件路径。“推断的基础 data flow”不是 runtime trace 或经过验证的真实执行路径，必须在章节标题和正文中使用“推断”“可能”或类似标签，不得伪装成已验证事实。

### 6.8 CLI 体验

核心交互保持单一：

```text
repolens analyze <github-url>
```

必要 options 控制在较小范围：

- `--output`：指定报告路径；
- `--model`：覆盖默认模型；
- `--max-files`：限制候选文件数量；
- `--verbose`：显示更详细的处理信息。

运行时应显示简洁的阶段进度，例如 cloning、scanning、summarizing 和 writing report，但不需要复杂的 interactive UI。

## 7. 功能需求

| 编号 | 需求 | 优先级 |
|---|---|---|
| FR-01 | 接收并验证公开 GitHub repository URL | Must |
| FR-02 | shallow clone default branch 到临时目录 | Must |
| FR-03 | 生成过滤后的 directory tree | Must |
| FR-04 | 识别主要语言、framework 和 dependency manifest；JavaScript/TypeScript、Python 为优先语言 | Must |
| FR-05 | 按规则筛选和排序重要文件 | Must |
| FR-06 | 为 JavaScript/TypeScript 和 Python 提取轻量级模块关系线索；其他语言仅做通用目录和文件级分析 | Must |
| FR-07 | 分批调用 LLM 并控制 context 大小 | Must |
| FR-08 | 生成固定结构的 `PROJECT_MAP.md` | Must |
| FR-09 | 标注分析范围、限制和推断 | Must |
| FR-10 | 为常见失败提供可操作的 CLI 错误提示 | Must |
| FR-11 | 支持自定义输出路径和模型 | Should |
| FR-12 | 显示阶段进度和 token/cost 相关统计 | Should |

## 8. 非功能需求

### 8.1 安全

- 不执行、import、build 或 test 目标仓库；
- 不主动读取或上传疑似 secrets；
- 防止 symlink 和 path traversal 逃出临时工作目录；
- prompt 明确隔离 instructions 与 repository content；
- 日志不得输出 API key 或完整敏感内容。

### 8.2 性能与成本

- 对常见小型仓库，应在合理的 LLM 调用次数内完成；
- 对超大仓库应提前限制扫描和上下文，而不是无限处理；
- 相同输入的文件排序应尽量 deterministic；
- 失败重试应有次数上限，不进行无限 retry。

### 8.3 可维护性

- static analysis 与 LLM provider 解耦；
- 每个 component 有清晰职责和可测试接口；
- 核心流程可以使用 Mock LLM 完成离线测试；
- 默认配置集中管理，不散落 magic numbers。

### 8.4 可用性

- 安装和首次运行步骤面向初学者书写；
- 错误信息说明“发生了什么”和“如何修复”；
- 默认行为可直接使用，不要求用户理解内部分析策略。

## 9. MVP 验收标准

v0.1 可发布必须满足：

- 能对至少一组公开、不同技术栈的 fixture repositories 完成端到端分析；
- 每次成功运行都会生成包含规定九个部分的 `PROJECT_MAP.md`；
- 技术栈结论能引用 manifest 或配置文件作为依据；
- 重要文件说明包含可定位的相对路径；
- 报告明确披露被跳过的文件、规模限制和推断内容；
- JavaScript/TypeScript 和 Python fixtures 能生成轻量模块关系及明确标记为推断的基础 data flow；
- 其他语言 fixtures 只要求生成通用目录、文件、配置和技术栈概览，不要求语言专用关系；
- 无效 URL、clone 失败、Git 缺失、API key 缺失和 LLM 失败均有明确错误；
- 测试不依赖真实 LLM API；
- 默认流程不会执行目标 repository 中的代码；
- 项目具备 `README.md`、`LICENSE`、安装指南、使用示例和一份 sample `PROJECT_MAP.md`；
- 初学者能在干净环境中按照安装指南和使用示例完成首次分析。

## 10. 产品成功指标

v0.1 重点验证“报告是否有用”，不追求用户规模：

- 新用户可在 10 分钟内完成安装和首次运行；
- 试用者能通过报告正确指出项目用途、主要技术栈和核心入口；
- 大多数测试仓库的报告不缺少规定章节；
- 因输入或配置导致的失败均能给出下一步行动；
- 首批 open-source feedback 中，用户认为报告能减少初次浏览仓库的时间。

这些是产品验证指标，不是对所有环境的性能保证。

## 11. Future Features

### v0.2 候选

- 支持 local repository path；
- 支持 branch、tag 或 commit；
- 增量缓存，减少重复 LLM 调用；
- 增加 Anthropic、Ollama 等 provider；
- 更细的成本估算和 analysis profile；
- 改进 JavaScript/TypeScript 和 Python 的 import relationship 提取，并根据用户需求评估新的优先语言；
- 支持 JSON 中间产物和 machine-readable report；
- 允许 repository 级配置文件。

### v1.0 候选

- 稳定的 plugin/provider interface；
- 可扩展的 language analyzer；
- report diff，比较两个 commit 的架构变化；
- GitHub Action 或 CI integration；
- 可选 Web interface；
- 面向大型 monorepo 的子项目识别和选择性分析。

Future Features 仅表达方向，不属于 v0.1 承诺。

## 12. 初期明确不构建

以下内容不进入 v0.1：

- Web UI；
- 用户账户、authentication 和 authorization；
- database 或长期 server-side storage；
- 私有 GitHub repository；
- GitHub OAuth 或 GitHub App；
- full AST engine；
- 精确 call graph 或 runtime trace；
- autonomous agent exploration；
- 自动执行 build、test、dependency install 或 repository code；
- 自动修改代码、生成 pull request 或提交 commit；
- security vulnerability scanner；
- IDE extension；
- 实时多人协作；
- self-hosted web service；
- 对所有 programming languages 的专用深度分析。

## 13. Open-source 发布要求

### 13.1 v0.1 必需发布内容

为降低采用门槛，v0.1 release 必须具备：

- `README.md`，清晰说明项目定位、适用范围和已知限制；
- 面向初学者的安装指南和 Quick Start；
- 至少一个可复制的 CLI 使用示例；
- 至少一份由公开 repository 生成的 sample `PROJECT_MAP.md`；
- 明确的 API key、数据发送和成本说明；
- `LICENSE`，建议使用 Apache-2.0 或 MIT；
- 基础 CI，包括 lint、test 和 package build；
- 语义化版本和简洁 changelog；
- 对“分析结论可能出错”的明确免责声明。

### 13.2 可选发布完善项

以下内容有助于 open-source community 建设，但不作为 v0.1 发布阻塞条件：

- `CONTRIBUTING.md`；
- `CODE_OF_CONDUCT.md`；
- bug report 与 feature request issue templates；
- 更完整的 maintainer 和 contributor workflow 文档。

README 可以在发布阶段采用中英文双语；本阶段内部文档保持中文。

## 14. 主要风险与应对

| 风险 | 影响 | v0.1 应对 |
|---|---|---|
| LLM hallucination | 报告包含错误结论 | 引用文件路径、标记推断、保留限制章节 |
| 大型仓库超出 context | 成本和延迟失控 | 扫描上限、重要性排序、分层总结 |
| Repository prompt injection | 模型被恶意文本误导 | 内容视为数据、固定 system prompt、不执行指令 |
| 意外上传 secret | 安全和信任受损 | 敏感路径过滤、日志脱敏、文档披露 |
| 多语言分析过浅 | 报告质量不一致 | 优先支持 JavaScript/TypeScript 和 Python；其他语言只承诺通用目录和文件级分析 |
| 初学者配置困难 | 首次运行失败 | Quick Start、环境检查、可操作错误信息 |
| Provider 变化 | 集成维护成本 | 使用隔离的 provider interface |
