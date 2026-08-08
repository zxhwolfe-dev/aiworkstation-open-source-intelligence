# AI Open Source Intelligence 一键产品形态

## 最终目标

最终产品不是“用户先安装 Skills，再自己研究 MCP 怎么配”。

用户应该只感知一个产品：

```text
安装 AI Open Source Intelligence
        |
     登录/授权一次
        |
ChatGPT / Codex / MCP Host
        |
3 个 Skills + Hosted MCP
        |
AI 开源项目雷达实时数据
```

用户不需要：

- clone GitHub 仓库；
- 安装 Python；
- 手动配置你的数据库；
- 复制 API Key；
- 理解 Skills 与 MCP 的技术区别。

## 9 个标准实时能力

Hosted MCP 提供 9 个普通数据/研究工具：

1. `search_ai_projects` — 按自然语言需求找项目；
2. `get_project_facts` — 核验项目当前公开事实；
3. `get_license_evidence` — 核验许可证直接证据；
4. `compare_ai_projects` — 项目对比；
5. `find_alternatives` — 找替代项目；
6. `compose_ai_stack` — 组合候选技术栈；
7. `get_radar_overview` — 查看当前所有榜单、合集、分类、场景等导航维度；
8. `browse_radar_projects` — 按榜单/合集/分类/场景/License/部署方式等浏览项目；
9. `browse_radar_skills` — 浏览、搜索、筛选 Skills 库以及查看单个 Skill 详情。

这三个 browse 工具故意做得比较宽，不把网站每一个 URL 都做成一个 MCP Tool。这样用户好用、模型好选工具、平台审核也清晰。

### 用户可以直接这样问

- “今天 AI 开源项目榜单有什么？”
- “有哪些合集？”
- “看看 RAG 分类。”
- “找支持 Docker 私有部署的项目。”
- “Dify 和 RAGFlow 哪个更适合内部知识库？”
- “有哪些代码审查 Skills？”
- “打开这个 Skill，告诉我怎么用。”

## Premium AI：第 10 个工具

Hosted 产品额外提供：

```text
deep_research_ai_projects
```

它才会使用 AI Workstation 服务器端的大模型。

普通 9 个工具：

```text
实时数据库 / 索引 / 筛选 / Evidence
→ 不消耗 Premium AI Credits
```

Premium：

```text
用户提出深度研究任务
→ 先用规则/数据库筛出公共 Radar 结果
→ 只把受控公共上下文交给服务器模型
→ 生成深度研究/对比/技术栈/市场扫描分析
```

模型生成内容仍然是分析/建议，不会被冒充成 verified facts。

## 免费一次与付费

第一版策略：

```text
9 个普通 Radar 工具
→ 免费使用（受 OAuth 用户限流）

Premium AI
→ 第一次成功任务免费
→ 模型失败不消耗免费机会
→ 之后使用 AI Credits
```

初始 Pro 代码配置按每月 50 AI Research Credits 设计，但最终价格在正式 Paddle 商品中配置，不写死在代码里。

### 为什么按任务/credits，而不是 Token 收费

用户更容易理解：

> “本月还有 34 次 AI 深度研究额度”

而不是：

> “还剩 1,830,471 tokens”。

以后可以让小任务消耗 1 Credit，大型报告消耗 3 Credits。

## 支付体验

第一版国际付费适配 Paddle，但 entitlement 是支付平台无关的，所以未来可以增加其他支付方式。

用户流程：

```text
第一次 Premium
→ 免费完成

第二次 Premium，无额度
→ 返回“需要升级”
→ 给出 HTTPS Paddle Checkout 链接
→ 用户浏览器支付
→ Paddle webhook 验签
→ 后台给同一个 OAuth 用户更新 Pro/credits
→ 回到 ChatGPT/Codex 继续用
→ 无需重新安装
```

支付 webhook 有：

- 原始 body HMAC 验签；
- 时间戳容差；
- `(provider, event_id)` 数据库唯一约束；
- webhook 重试不会重复充值；
- 旧事件不能覆盖较新的 canceled/past_due 状态；
- 只有识别到正式 Pro price 的成功付款事件才发放/重置 credits。

Active Pro 用户本月 credits 用完时，不能再自动创建第二份 Pro 订阅。未来如果需要，可以单独卖一次性 top-up credits。

## OAuth 登录

正式 Hosted MCP 使用标准 OAuth resource-server 模式。

用户授权后的 `(issuer, subject)` 会先转换成不可逆内部 ID：

```text
issuer + subject
→ SHA-256
→ oidc_<opaque-id>
```

后台 entitlement、试用和限流都使用这个 opaque ID。

不会把下面内容暴露到 Tool 返回、模型 Prompt 或支付 custom_data：

- OAuth bearer token；
- 原始 OAuth subject；
- MCP backend service token；
- Paddle customer/subscription ID。

## 限流

Hosted 初始默认：

```text
普通工具：60 次/分钟，300 次/小时
Premium：  5 次/分钟 + entitlement/credits
```

计数对象是经过 OAuth 验证后的用户身份，不是 IP，也不是用户自己提交的用户名。

## 当前状态

代码已经进入 Hosted 产品候选阶段，但还不能声称公网正式上线。

上线前仍要完成真实执行：

1. 全量测试与 CI；
2. EN/ZH 榜单/合集/分类/Skills live browse 验证；
3. 配置真实 OAuth provider；
4. 部署正式 HTTPS `/mcp`；
5. 从 ChatGPT/Codex 完成真实 OAuth 登录和 9 工具 remote smoke；
6. Paddle sandbox 完成购买/续费/失败/取消 webhook 全链路；
7. 验证 Premium 第一次免费、第二次升级、付款后继续使用；
8. 完成正式隐私、条款、退款与数据保留说明；
9. 注册并提交 Skills + MCP 的最终 Plugin。
