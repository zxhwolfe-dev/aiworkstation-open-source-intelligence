# 一次安装产品说明

## 当前产品形态

AI Open Source Intelligence 0.3 由一个统一 Skill 和九个匿名、只读、仅数据/证据的 MCP 工具组成。Host 模型负责理解、推理和最终回答；AI Workstation 只提供公共 Radar 数据与证据。

当前版本没有 OAuth、会员、支付、Credits、Checkout、Premium 工具或 AI Workstation 服务器模型调用，也不存在可重新开启这些能力的环境变量。

仓库 Plugin 已通过 `.mcp.json` 把统一 Skill 与生产 Hosted MCP 配置放进同一
安装包。该改动进入 `main` 后，Codex 与 ChatGPT 桌面版的 Codex Host 可以从
一个 Marketplace 条目安装完整 Plugin。已发布的 `v0.3.0` 压缩包仍是不可变
的 Skills-only 历史制品，完整包使用 `v0.3.1` 补丁版本，不能覆盖重建。

ChatGPT 网页端在公共目录审核前仍需先注册 Developer-mode MCP 连接；正式
提交必须选择 **With MCP / Universal / No Authentication**。因此可以对
Codex Alpha 宣传“一次安装”，但在公共目录审核通过前，不能对所有 ChatGPT
普通用户宣传已经实现公共一键安装。

## 九个工具

`search_ai_projects`、`get_project_facts`、`get_license_evidence`、`compare_ai_projects`、`find_alternatives`、`compose_ai_stack`、`get_radar_overview`、`browse_radar_projects`、`browse_radar_skills`。

所有结果使用 `osi.tool-result.v2`，严格分开：

1. `verified_facts`：有公开来源支持的事实；
2. `recommendations`：规则或 Host 模型分析；
3. `unknowns`：尚未验证或无法获取的信息；
4. `risks`：License、部署、维护、安全与兼容性风险。

## 约束契约

项目搜索、替代方案和技术栈规划使用类型化约束：

```json
[{"id":"deployment","value":"self-hosted","polarity":"required"}]
```

`polarity` 只能是 `required`、`preferred` 或 `excluded`。无法支持的 `required` 条件会明确失败并列出阻断原因，避免系统假装满足用户的硬要求；非硬条件不会冒充硬约束。旧参数 `source_mode` 已删除。

## 只读与执行效果

只读表示不修改用户或第三方业务数据。需求搜索在实现层可能创建、轮询或取消短期 selector 计算任务；`execution.business_data_write=false`，控制面效果通过 `ephemeral_control_plane_effects` 公开披露。

工具不会安装或执行第三方仓库代码，不会把缺失 License 推断为可使用，也不会为了生成结果静默放宽硬条件。

## Hosted

正式端点是 `https://mcp.aiworkstation.cn/mcp`。当前只支持匿名 data-only 模式，由 TLS/Nginx 网关提供 body、连接和 IP 防刷控制。候选容器必须同时携带并校验精确的 release SHA 与 image SHA。

任何未来的身份、付费或服务器模型能力都必须作为新版本重新设计、实现和完成法律/安全审核，不能作为 0.3 的隐藏功能。
