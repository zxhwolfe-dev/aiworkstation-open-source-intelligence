# AI Open Source Intelligence

**面向开源 AI 项目的证据化研究、Radar 浏览、项目对比、许可证核验与技术选型工具。**

[English](README.md) · [快速开始](docs/QUICKSTART.md) · [FAQ](docs/FAQ.md) · [AI 开源项目雷达](https://aiworkstation.cn/githubai/)

> 3 个 Skills · 9 个标准只读 MCP 工具 · 中英文工作流 · Apache-2.0

AI Open Source Intelligence 是 AI Workstation 面向开源 AI 生态构建的 Skills/MCP 产品层。它帮助开发者、技术负责人和 AI 创业者发现、核验、比较开源项目，并始终把 **已验证事实、分析建议、未知信息和风险** 分开。

## 默认产品体验

第一阶段 Hosted 产品保持简单：

```text
安装 / 连接一次
      |
      v
3 个 Skills + 公网 Hosted MCP
      |
      v
9 个实时只读 Radar 工具
      |
      v
AI Workstation 公共 Radar 数据
```

这 9 个标准工具**不要求 WorkOS、不要求其他 OAuth 服务、不要求付款、不要求 Premium 后端，也不另建一套 OSI 会员体系**。

未来会员/Premium 能力将接入现有 **AI Workstation 会员体系**，而不是重新建立一套互相独立的 Pro/credits 用户系统。

## 它能做什么？

- **找项目**：根据 Docker、自托管、Web UI、隐私、预算等条件筛选开源 AI 项目；
- **查项目**：核验指定项目的当前公开事实；
- **查许可证**：只有直接公开证据才能提升为已核验 License；
- **做对比**：在明确使用场景下比较 2–5 个项目；
- **找替代**：在不偷偷放宽硬条件的前提下寻找替代方案；
- **配技术栈**：组合候选开源 AI 技术栈并暴露兼容性未知项；
- **浏览 Radar**：浏览榜单、合集、分类、场景、项目目录和 Skills 库。

## 证据边界

每个标准工具结果都会区分：

```text
data
verified_facts
recommendations
unknowns
risks
```

`data` 里出现一个字段并不自动代表它已经成为“已验证事实”。许可证结果是技术证据，不是法律意见；没有直接证据时必须保持 unknown。

## 三个 Skills

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

Skills 负责可复用的安全研究流程，Hosted MCP 负责提供当前 Radar 数据。

## 9 个标准只读 MCP 工具

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

它们都不会修改 GitHub、AI Workstation 或第三方项目，也不会安装/执行第三方仓库代码。

## 本地开发模式

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

离线 mock：

```bash
OSI_PROVIDER=mock osi-mcp
```

连接线上公共 Radar 数据：

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

## Hosted 模式

生产入口：

```bash
osi-mcp-hosted --check-config
```

### `public` — 默认模式

```text
OSI_HOSTED_ACCESS_MODE=public
```

特点：

- 恰好 9 个标准只读工具；
- 匿名使用，不要求登录；
- 不加载 WorkOS/OAuth 配置；
- 不加载 Premium/会员后端；
- 不暴露 Premium 工具；
- 继续保留 Git candidate → Docker image → runtime → `serverInfo.version` 的精确 SHA 身份链；
- 公网必须经过 HTTPS + Nginx 单 IP 请求/并发连接防刷边界；
- Hosted 容器只绑定主机 `127.0.0.1:8001`。

### `oauth` — 可选兼容/未来会员模式

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

现有标准 OAuth Resource Server 能力继续保留，并兼容当前 `deep_research_ai_projects` Premium 合同。WorkOS 只是其中一个可替换 OAuth 提供商，不再是免费 Hosted MCP 的依赖。

## 会员与收费

这个项目**不再设计第二套独立 OSI 会员体系**。

未来目标是：

```text
                    AI Workstation 会员
                            |
                +-----------+-----------+
                |                       |
           网站使用入口             Skills / MCP
                |                       |
                +-----------+-----------+
                            |
                    统一 AI 用量策略
```

现阶段 AI Workstation 现有人工收费流程可以继续：用户通过微信、邮箱或线下联系完成付款，再由现有会员/邀请码体系开通权益。

未来如果使用 Paddle 或其他支付平台，它只应作为“自动收银台/自动开通适配器”，把付款结果写回同一 AI Workstation 会员体系，而不是创建第二套 OSI 订阅数据库。

邀请码/激活码**绝不能直接作为 MCP Bearer Token、Authorization 凭据或普通 Tool 参数**。未来会员绑定必须通过经过安全设计的一方网页或标准身份流程完成。

详见 [`docs/MEMBERSHIP-AND-MONETIZATION.md`](docs/MEMBERSHIP-AND-MONETIZATION.md)。

## Premium 深研

代码仍保留 OAuth 兼容模式下的：

```text
deep_research_ai_projects
```

但它**不会出现在默认 `public` Hosted 模式中**。在真正付费上线前，其权益与用量语义必须改为接入 AI Workstation 现有会员/额度体系，而不能把现有“独立 credits”当作最终商业方案。

## Hosted 验收

默认公网 Hosted 的正式 smoke：

```bash
osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted-public \
  --auth-mode none \
  --output tmp/hosted-remote.json
```

它验证：

- 本地候选 SHA 与 Docker/远端部署 SHA 完全一致；
- HTTPS 网关存在；
- Nginx IP 请求/连接防刷策略已配置；
- 恰好 9 个只读工具；
- 真实公网 `search_ai_projects` 调用成功；
- MCP 协议版本已协商并记录。

OAuth 模式仍可单独使用 `--profile hosted-oauth` 验证。

## 当前状态

**Hosted candidate 开发阶段，尚未宣称广泛公开上线。**

当前路线明确拆成两步：

1. 先上线匿名、只读、无需 WorkOS/支付的 9 工具 Hosted MCP；
2. 等真实使用需求验证后，再设计 MCP 客户端与 AI Workstation 会员的安全绑定，并在此基础上开启会员/Premium 能力。

自动支付不是 Hosted Private Alpha 的门槛。

## 开发

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
osi-validate-plugin --root .
```

CI 覆盖 Python 3.10 和 3.12。

## 文档

- [`docs/hosted-private-alpha.md`](docs/hosted-private-alpha.md)
- [`docs/MEMBERSHIP-AND-MONETIZATION.md`](docs/MEMBERSHIP-AND-MONETIZATION.md)
- [`docs/HOSTED-OAUTH.md`](docs/HOSTED-OAUTH.md)
- [`docs/ONE-INSTALL-PRODUCT.md`](docs/ONE-INSTALL-PRODUCT.md)
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md)
- [`docs/FAQ.md`](docs/FAQ.md)
- [`SECURITY.md`](SECURITY.md)
- [`PRIVACY.md`](PRIVACY.md)

## License

本公开仓库采用 [Apache License 2.0](LICENSE)。Apache-2.0 只覆盖这个公开仓库，不自动覆盖 AI Workstation 私有数据库、未公开数据、私有后台、托管基础设施或商标。
