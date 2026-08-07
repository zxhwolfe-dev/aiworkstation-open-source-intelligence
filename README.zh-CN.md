# AI Open Source Intelligence

**面向开源 AI 项目的证据化研究、项目对比、许可证核验与技术选型工具。**

[English](README.md) · [快速开始](docs/QUICKSTART.md) · [FAQ](docs/FAQ.md) · [产品网站](https://aiworkstation.cn/githubai/)

> 3 个 Skills · 6 个只读 MCP 工具 · 中英文工作流 · Apache-2.0

AI Open Source Intelligence 是 AI Workstation 面向开源 AI 生态构建的研究与技术选型层。它帮助开发者、技术负责人和 AI 创业者从真实约束出发发现、核验、比较开源项目，并设计候选技术栈，同时始终把 **已验证事实、分析建议、未知信息和风险** 分开。

## 它解决什么问题？

普通大模型很擅长解释和推理，但开源项目的版本、活跃度、部署方式、许可证和文档会不断变化。这个项目的目标不是“再做一个聊天机器人”，而是给 AI 一个更严格的开源项目研究流程和结构化数据接口。

你可以用它来：

- **找项目**：根据 Docker、私有部署、Web UI、隐私、预算等条件筛选开源 AI 项目；
- **查项目**：核验一个指定项目的当前公开事实；
- **查许可证**：区分“页面上出现一个 License 标签”和“有直接可核验 License 证据”；
- **做对比**：在明确使用场景下比较 2–5 个项目；
- **找替代**：在不放宽硬条件的前提下寻找替代项目；
- **配技术栈**：从业务目标出发组合候选 RAG / Agent / 内部知识库技术栈。

## 与普通 AI 推荐有什么不同？

### 1. 事实和分析分开

每个工具结果都明确区分：

```text
data
verified_facts
recommendations
unknowns
risks
```

`data` 中出现一个字段，并不代表它已经成为“已验证事实”。

### 2. 字段有证据等级

当前 live provider 使用：

```text
verified_public_metadata
verified_direct_evidence
public_projection_only
unknown
```

### 3. License 更严格

许可证标签本身不自动等于“已验证许可证”。如果缺少直接公开 License 证据，结果会保持 unknown，并提示 `LICENSE_UNVERIFIED` 风险。许可证结果是技术证据，不是法律意见。

### 4. 不偷偷放宽硬条件

如果用户要求 Docker + 私有部署 + Web UI，而没有项目完整满足，正确结果是明确 `no_match`，而不是偷偷删掉某个条件。

### 5. Near Match 不冒充正式匹配

接近匹配的项目必须单独显示，并说明阻塞条件。

### 6. 项目对比使用兼容 Snapshot

不会把不同时间状态的数据混在一起当成同一时点比较。

## 三个 Skills

### `open-source-project-research`

从用户任务、部署、隐私、预算、License 和技术能力出发发现或核验开源 AI 项目。

### `open-source-project-comparison`

在具体使用场景下比较 2–5 个开源 AI 项目，并明确事实、权衡、未知项和可能改变结论的条件。

### `open-source-stack-planner`

先拆解系统角色，再设计候选技术栈。单个项目事实可以被核验，但跨项目兼容性在真正测试前仍保持“未验证”。

## 六个只读 MCP 工具

| 工具 | 用途 |
| --- | --- |
| `search_ai_projects` | 根据任务和约束寻找项目 |
| `get_project_facts` | 获取一个项目的当前公开事实与证据状态 |
| `get_license_evidence` | 核验直接许可证证据 |
| `compare_ai_projects` | 比较 2–5 个项目 |
| `find_alternatives` | 在约束下寻找替代项目 |
| `compose_ai_stack` | 组合候选开源 AI 技术栈 |

所有当前产品工具都是只读的，不会修改 GitHub，不会安装或执行第三方仓库代码。

## 使用方式

### 方式 A：只安装 Skills

```bash
codex plugin marketplace add zxhwolfe-dev/aiworkstation-open-source-intelligence --ref main
codex plugin marketplace list
```

**Skills-only 不会直接连接 AI Workstation 的线上项目数据库。**

没有 live MCP 时，Skills 仍然可以：

- 理解需求；
- 区分硬条件和偏好；
- 生成选型矩阵；
- 设计验证流程；
- 做角色级架构规划。

但它不能声称自己拿到了当前数据库里的实时项目或许可证事实。

### 方式 B：本地 MCP（当前功能最完整）

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

先使用离线 mock：

```bash
OSI_PROVIDER=mock osi-mcp
```

再启用线上只读 Radar 数据：

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

详见 [`docs/codex-setup.md`](docs/codex-setup.md)。

### 方式 C：CLI

```bash
osi-m0 provider-info
osi-m0 list-tools
osi-m0 invoke search_ai_projects \
  --arguments '{"query":"找一个支持 Docker、私有部署和 Web UI 的 RAG 项目","locale":"zh"}'
```

## 搜索会不会额外调用 AI Workstation 的大模型？

当前 M1 live provider 向 Radar selector 发送 `use_model=false`。

因此当前六工具的主搜索/检索路径不要求 AI Workstation 后台再额外调用一次付费 LLM。ChatGPT、Codex 或其他 MCP Host 自己的模型负责理解问题、选择工具和生成最终回复；AI Workstation MCP 负责结构化数据检索和证据返回。

详见 [`docs/MODEL-AND-DATA-FLOW.md`](docs/MODEL-AND-DATA-FLOW.md)。

## MCP 等于整个 AI Workstation 网站吗？

不是。

MCP 只能使用**明确暴露为 Tool 的能力**。当前六个工具覆盖的是 Open Source Intelligence / Open Source Radar 的核心研究决策流程，不代表已经开放 AI Workstation 网站的全部功能、账号能力、内部管理接口或私有数据库操作。

以后需要开放新的线上能力，应单独设计新的只读/鉴权 Tool，而不是默认把整个网站后台暴露给 MCP。

## Quick Start

查看 [`docs/QUICKSTART.md`](docs/QUICKSTART.md)。

## 常见问题

查看 [`docs/FAQ.md`](docs/FAQ.md)。

## 开发

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
python -m compileall -q src tests
python -m unittest discover -s tests -v
osi-validate-plugin --root .
```

CI 覆盖 Python 3.10 和 3.12。

## 项目结构

```text
.codex-plugin/         Plugin manifest
.agents/plugins/       Repo marketplace
skills/                三个 Skills
src/aiworkstation_osi/ 核心、Provider、MCP、验证工具
schemas/               工具和结果契约
evals/                 中英文评测案例
tests/                 自动化测试
docs/                  架构、部署、发布和使用文档
```

## 当前状态

项目已经通过 Skills-only External Alpha 的机器与人工验收。Broad public hosted MCP 仍是独立阶段，需要完善最终身份认证、撤销、额度、限流、滥用控制、生产监控及托管服务法律/隐私策略。

查看 [`ROADMAP.md`](ROADMAP.md)。

## 参与贡献

查看 [`CONTRIBUTING.md`](CONTRIBUTING.md) 和 [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)。

普通缺陷请使用 GitHub Issue 模板；安全问题请按 [`SECURITY.md`](SECURITY.md) 私下报告。

## License

本公开仓库采用 [Apache License 2.0](LICENSE)。

**注意：** Apache-2.0 只覆盖这个公开仓库，不自动覆盖 AI Workstation 的私有数据库、未公开数据集、私有后台、托管基础设施或商标。
