# AI Open Source Intelligence

**一个 Skill，9 个实时只读 Radar 工具；做开源 AI 研究、对比和选型，不再额外调用一遍 AI Workstation 服务器大模型。**

[English](README.md) · [AI Workstation](https://aiworkstation.cn/) · [AI 开源项目雷达](https://aiworkstation.cn/githubai/) · [快速开始](docs/QUICKSTART.md)

AI Open Source Intelligence 是 **AI Open Source Radar / AI 开源项目雷达** 的 Skills + MCP 产品层。

## 产品形态

```text
ChatGPT / Codex / 兼容 Host 中的用户
                 |
                 v
           1 个统一 Skill
                 |
                 v
          9 个只读 MCP 工具
                 |
                 v
       AI Workstation 公共 Radar 数据
```

用户不需要在“项目研究 / 项目对比 / 技术栈规划”三个 Skill 之间做选择。统一 Skill 会自己判断任务并调用合适的工具。

自然语言理解、推理和最终整理都由**用户正在使用的 Host 模型**完成；AI Workstation 在这条产品路径上只提供数据和证据。

## 只有一个正式 Skill

```text
ai-open-source-intelligence
```

它统一处理：

- 浏览日/周/月榜、合集、分类、场景和 Radar Skills；
- 根据部署、隐私、集成、预算、License 等要求找项目；
- 核验指定项目事实和 License 证据；
- 对比 2–5 个项目；
- 在不放宽硬条件的情况下找替代；
- 规划候选开源 AI 技术栈，并明确兼容性未知项。

唯一正式 Skill 来自：

```text
product-skills/ai-open-source-intelligence/SKILL.md
```

之前拆开的“项目研究 / 项目对比 / 技术栈规划”三个 Skill 文件已从当前产品和分发包中彻底移除。

## 9 个标准 MCP 工具

```text
search_ai_projects
get_project_facts
get_license_evidence
compare_ai_projects
find_alternatives
compose_ai_stack
get_radar_overview
browse_radar_projects
browse_radar_skills
```

全部只读，不执行、不安装第三方仓库代码。

## 明确禁止走 AI Workstation 服务器大模型

这是当前版本的硬边界。

Hosted MCP 不提供 Premium 模型工具、不提供支付/credits 工具，也不存在通过环境变量重新打开 OAuth/Premium 的隐藏开关。

需求型项目搜索调用公开 Radar selector 时固定：

```text
use_model=false
```

因此正常链路是：

```text
ChatGPT / Codex 的模型
        -> 理解问题、选择工具
        -> AI Workstation 返回公共 Radar 数据/证据
        -> ChatGPT / Codex 整理最终回答
```

而不是：

```text
用户模型 -> AI Workstation 再调一次模型 -> 双重模型成本
```

以后如果要做会员服务器模型能力，必须作为新版本重新设计、评审和验收，不能靠现在的环境变量偷偷打开。

## 证据边界

所有工具结果继续严格区分：

1. **verified facts**：有当前公开证据支持的事实；
2. **recommendations**：Host 模型/规则分析；
3. **unknowns**：无法确认或尚未验证的信息；
4. **risks**：License、维护、部署、安全和集成风险。

`data` 里出现一个字段不代表它已经是“已验证事实”。License 证据更严格，并且只是技术证据，不是法律意见。

## 返回内容中的官方入口

每个 MCP 工具结果都会在：

```text
data.official_resources
```

中附带固定、不带追踪参数的官方入口：

- AI Workstation：https://aiworkstation.cn/
- AI 开源项目雷达：https://aiworkstation.cn/githubai/
- 开源项目：https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence

统一 Skill 可以在正常用户回答结尾最多展示一次“官方资源”。这些链接与 verified facts 分离，不会混入研究结论。

## Hosted MCP

正式地址：

```text
https://mcp.aiworkstation.cn/mcp
```

当前模式固定为：

```text
匿名
只读
仅数据/证据
9 个工具
无 OAuth
无 WorkOS 依赖
无 Premium/服务器模型
```

容器只监听宿主机 `127.0.0.1:8001`，外面由 Nginx/TLS 代理。

### 匿名防刷

公网网关使用两层 IP 请求限流 + 并发限制：

- 短时：`60 次/分钟`，burst `30`；
- 持续：`10 次/分钟`，burst `300`；
- 每 IP 并发连接：`10`；
- MCP body 最大：`256 KB`；
- 专用 MCP 域名其他路径直接 `404`。

这里按“请求次数”限制，而不是按网站 10 万/100 万 Token 限制，因为这 9 个数据工具不消耗 AI Workstation 模型 Token。

## 现在如何使用

仓库 Plugin 现在已经把统一 Skill 与生产 Hosted MCP 配置打在一起。该改动
进入 `main` 后，Codex 与 ChatGPT 桌面版的 Codex Host 可从一个 Marketplace
条目同时安装两者；ChatGPT 公共目录仍在等待审核。当前可用方式：

- Codex / ChatGPT 桌面版：安装完整的仓库 Plugin；
- ChatGPT 网页端：公共目录上架前，在 Developer mode 中把
  `https://mcp.aiworkstation.cn/mcp` 注册为 **No Authentication** 应用；
- Python/CLI：`v0.3.1` 发布后，安装同版本包：

```bash
python -m pip install \
  "aiworkstation-open-source-intelligence[mcp]==0.3.1"
```

具体步骤见[快速开始](docs/QUICKSTART.md)。不可变的 `v0.3.0` 压缩包仍是旧的
Skills-only 制品；完整 Plugin 使用 `v0.3.1` 补丁版本发布，不能覆盖重建
`v0.3.0`。

## 本地开发

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

离线：

```bash
OSI_PROVIDER=mock osi-mcp
```

线上公共 Radar：

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

当前版本设置：

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

会直接 fail-closed。

## 安全规则

- 不执行第三方仓库代码；
- 不从“没有 License”推断“可以商用”；
- 不为了给出结果偷偷放宽硬条件；
- 没有证据或受控测试时不声称跨项目兼容；
- live evidence 不可用时不拿模型记忆冒充实时事实；
- 当前标准 Skill/MCP 路径永远不调用 AI Workstation 服务器大模型。

## License

公开仓库采用 Apache-2.0。它不自动授权 AI Workstation 私有数据库、未公开数据、服务器凭据、基础设施或商标。
