# Website Launch Copy

Copy for the public AI Workstation product page. Adapt layout/SEO metadata to the website implementation without changing product claims.

## English

### SEO title

AI Open Source Intelligence — Evidence-backed Open Source AI Research

### Meta description

Research, compare, verify, and select open-source AI projects with evidence-backed workflows, license verification, explicit unknowns, and read-only MCP tools.

### Hero

**Choose open-source AI projects with evidence, not memory.**

Research, compare, verify licenses, find alternatives, and design candidate AI stacks with explicit facts, unknowns, and risks.

Primary CTA: `Connect in ChatGPT (Developer mode)`

Secondary CTA: `Read the Quickstart`

Developer note: `View on GitHub`

### Core capabilities

**Find projects**  
Search from deployment, privacy, budget, and technical constraints.

**Verify facts**  
Keep current public facts separate from analysis and editorial projection.

**Verify license evidence**  
A visible label is not automatically treated as verified permission.

**Compare projects**  
Compare 2–5 projects in one explicit use case and compatible snapshot context.

**Find alternatives**  
Preserve hard requirements and expose the exact blocker for near matches.

**Compose a stack**  
Design a candidate open-source AI architecture while keeping integration compatibility unverified until tested.

### Why it is different

General AI models can reason about software, but project status and evidence change. AI Open Source Intelligence adds a maintained research contract:

- verified facts ≠ recommendations;
- missing evidence stays unknown;
- hard constraints are not silently relaxed;
- near matches are not promoted to full matches;
- license evidence has a stricter verification boundary;
- project comparison protects snapshot consistency.

### Distribution

**Unified Skill** — one portable research, comparison and stack-planning workflow.
**Hosted MCP** — nine anonymous read-only Radar tools at `https://mcp.aiworkstation.cn/mcp`.
**Local MCP / CLI** — published Python package for development, scripts and self-hosted integration.
**Public plugin** — combined one-install directory listing is pending platform review.

### Important boundary

The Skill package does not directly access the live AI Workstation database.
Current verified project data requires the companion Hosted or local MCP
connection. Before public plugin approval, those are two explicit setup steps.

### Open source

The public integration/plugin repository is Apache-2.0. Private AI Workstation databases, unpublished datasets, private backend systems, hosted infrastructure, and trademarks are not licensed merely because the public repository is open source.

### Hosted MCP privacy disclosure

The anonymous Hosted MCP receives only the fields submitted to a selected
tool: project queries or identifiers, typed constraints, locale, browsing
filters, and an optional caller-generated request ID. It does not receive the
complete ChatGPT or Codex conversation unless the host places that text in a
declared tool argument. Do not submit credentials, private source code, or
confidential documents.

The application does not create a database of MCP inputs or results. Its
privacy-safe operational telemetry excludes raw queries, constraints, result
payloads, credentials, cookies, and authorization headers. The public gateway
processes IP addresses in memory for TLS and abuse prevention. Its dedicated
access log stores only timestamp, HTTP status, total duration, and upstream
duration; it omits IP address, URI/query, referrer, User-Agent, and request
body. Security and error logs may contain network metadata including IP
addresses. Nginx logs rotate daily and retain 14 rotations.

For a privacy or deletion request concerning identifiable gateway log data,
email `zxhwolfe@gmail.com` with the relevant IP address and a narrow timestamp
range. Requests are processed where the record can be located, subject to
security, recovery, and legal retention needs. Do not send prompt text or
credentials in the request.

## 简体中文

### SEO 标题

AI Open Source Intelligence — 开源 AI 项目研究、对比与技术选型

### Meta Description

基于可核验证据研究、对比和选择开源 AI 项目，支持许可证核验、约束筛选、替代方案和候选技术栈规划，并明确区分事实、建议、未知信息和风险。

### Hero

**选开源 AI 项目，不靠模型记忆，靠可核验证据。**

发现项目、核验事实与许可证、比较方案、寻找替代项目，并设计候选 AI 技术栈。

主按钮：`在 ChatGPT Developer mode 中连接`
副按钮：`快速开始`

开发者入口：`GitHub`

### 核心能力

**找项目**  
根据私有部署、Docker、Web UI、隐私、预算和技术条件搜索项目。

**核验项目事实**  
把当前公开事实和分析/编辑性结论严格分开。

**核验许可证证据**  
页面上出现 License 标签，并不自动等于已确认商用许可。

**比较项目**  
在明确业务场景和兼容数据快照下比较 2–5 个项目。

**找替代**  
硬条件不偷偷放宽，Near Match 明确指出阻塞条件。

**组合技术栈**  
设计候选开源 AI 架构，同时把跨项目兼容性保持为“尚未验证”。

### 为什么不是普通 AI 推荐

普通大模型很会推理，但开源项目会更新。这个产品增加了一套持续维护的证据与选型边界：

- 已验证事实 ≠ AI 建议；
- 缺少证据就保持 unknown；
- hard requirements 不偷偷放宽；
- near match 不冒充正式匹配；
- License 使用更严格的直接证据门槛；
- 项目比较保护 snapshot 一致性。

### 使用方式

**统一 Skill** — 一个研究、对比和技术栈规划工作流。
**Hosted MCP** — `https://mcp.aiworkstation.cn/mcp` 提供 9 个匿名只读 Radar 工具。
**本地 MCP / CLI** — 已发布 Python 包，适合开发、脚本和自托管集成。
**公共插件** — Skill + Hosted MCP 的一次安装目录版本仍在等待平台审核。

### 重要边界

只安装 Skill **不会直接读取 AI Workstation 线上数据库**。要使用当前可核验的项目数据，需要连接 Hosted 或本地 MCP；公共插件审核通过前，这仍是两个明确步骤。

### 开源范围

公开插件/集成仓库采用 Apache-2.0；AI Workstation 私有数据库、未公开数据集、私有后台、托管基础设施和商标不因此自动开源。

### Hosted MCP 隐私说明

匿名 Hosted MCP 只接收用户提交给所选工具的字段：项目查询或标识符、结构化约束、语言、浏览筛选条件，以及可选的调用方 request ID。除非宿主主动把对话文本放入工具参数，否则服务不会收到完整的 ChatGPT 或 Codex 对话。请勿提交凭证、私有源代码或机密文档。

应用不会建立 MCP 输入或结果数据库。隐私化运行遥测不记录原始查询、约束、结果内容、凭证、Cookie 或 Authorization header。公网网关为 TLS 和防滥用在内存中处理 IP；专用 access log 只记录时间、HTTP 状态、总耗时和上游耗时，不记录 IP、URI/query、referrer、User-Agent 或 request body。安全和错误日志可能包含 IP 等网络元数据。Nginx 日志每日轮转，保留 14 个轮转文件。

如需对可识别的网关日志数据提出隐私或删除请求，请发送邮件至 `zxhwolfe@gmail.com`，提供相关 IP 和尽量精确的时间范围。运营方会在能够定位记录的情况下处理，并受安全、恢复和法律保留要求约束。请勿在请求中发送提示词或凭证。
