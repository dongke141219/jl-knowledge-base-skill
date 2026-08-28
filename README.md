# JL Private Knowledge Client

面向 Codex 的杰理（JL）公开工程壳与私有知识网关轻量客户端。外部用户可用公开工程壳在自己的电脑和 SDK 中完成检查、修改与 Makefile 编译；工程壳只为当前具体任务查询少量、带证据等级的知识片段，并在用户完成一次明确授权后，自动上传脱敏、结构化的待验证经验。

## 重要边界

- **本仓库不包含完整私有知识库**，也不包含客户源码、客户资料、网关凭据、密码、令牌、固件 KEY 或内网地址。
- 客户端不允许浏览、枚举、批量导出或重建完整知识库；每个任务最多只返回少量相关片段。
- 自动贡献只能进入 **未验证孵化库**，不会直接写入已验证知识。实际编译、实机结果和管理员晋级仍由服务端证据链决定。
- 外部用户或公司工程师使用的是**自己的 Codex/AI 账号与额度**。知识网关的查询、去重和存储本身不调用模型，不消耗知识库所有者的 Codex/AI token，也不会启动所有者的 Codex CLI。
- 本仓库提供 `jl-sdk-engineer-core` 公开工程壳和 `jl-private-knowledge-client` 知识伴随客户端，一次安装即可同时获得两者。公开工程壳只有通用施工、构建、证据和知识调用流程，不包含内部完整版 `jl-sdk-engineer` 的知识库、合作方资源、协议源码、静态库或客户资产。公司受控电脑仍可使用内部完整版代替公开工程壳。

共享的结构化索引以公司 NAS 数据库为权威来源；网页 worker、公司工程师和获授权的 GitHub 用户都通过受控 API/MCP 查询或提交。Windows 项目目录和 G 盘知识图只是项目记忆/本地镜像，完整源码、协议、静态库和合作方资源包仍只在公司受控电脑或 NAS 资产区，不进入本公开仓或公共查询结果。

## 当前可用状态

| 能力 | 状态 |
| --- | --- |
| 公开 JL SDK 工程壳（本地检查、修改、Makefile 编译与证据分级） | 已实现 |
| 私有知识查询/贡献伴随 Skill | 已实现 |
| 一次授权、可撤销、本地脱敏 outbox | 已实现 |
| 任务级知识查询与未验证贡献协议 | 已实现 |
| 正式公网 HTTPS 网关与生产身份认证 | **未上线** |

`skills/jl-private-knowledge-client/agents/openai.yaml` 中的 `example.invalid` 是故意保留的不可路由占位地址。因此，当前仓库可供审查、测试和开发，**不能宣称安装后已可直接连接私有知识库**。发布者必须先上线组织自有的 HTTPS MCP 网关和正式身份认证，然后只替换该 URL；不得把 token、密码、NAS 地址或客户信息写入本仓库。

生产身份认证还必须把“贡献同意版本”绑定到正式 OAuth/账号主体，并在用户关闭贡献时撤销服务端写权限。本地 `consent.json` 只负责一次提示、离线队列和客户端自动化，不能代替服务端授权控制。

## 工作方式

1. `jl-sdk-engineer-core` 只在当前用户提供的本地 SDK 中检查需求、修改源码或配置，并使用该工程自己的 Makefile/构建入口验证；它不会下载或复制公司的私有资产。
2. Codex 先检查当前 JL 项目证据，只在需要过往 JL 经验辅助决策时创建一个窄范围任务。
3. 网关仅返回与该任务匹配的少量片段，每条保留 E1/E2/E3 证据标签、适用范围和限制。
4. 完成有实质内容的 JL 实施、诊断、编译或实机验证后，Codex 从**本次工作自身证据**生成最小的结构化候选，不会把网关返回的私有片段再打包上传。
5. 候选先经过本地隐私校验并进入 outbox，再以稳定幂等键上传。断网、超时或限流不会导致主工程任务失败。
6. 服务端只确认 `accepted_to_incubator`；这代表进入未验证孵化库，不代表已验证。

详细调用契约见 [gateway-contract.md](skills/jl-private-knowledge-client/references/gateway-contract.md)，自动贡献与重试流程见 [contribution-workflow.md](skills/jl-private-knowledge-client/references/contribution-workflow.md)。

## 一次授权与关闭

安装、下载或查询本身都不等于同意自动贡献。首次需要自动贡献前，客户端必须先向用户说明上传边界并获得一次明确同意：

```text
python scripts/knowledge_outbox.py status
python scripts/knowledge_outbox.py grant --accept I_AGREE_TO_AUTOMATIC_SANITIZED_JL_KNOWLEDGE_CONTRIBUTION
```

授权后，后续有实质内容的 JL 任务会自动上传已脱敏候选，不再每次弹窗询问。用户可随时关闭，关闭时同时删除本地未发送候选：

```text
python scripts/knowledge_outbox.py revoke --confirm REVOKE_AND_DELETE_PENDING_CONTRIBUTIONS
```

默认不上传源码、原始日志、完整配置、客户/公司/项目名、本地或网络路径、文件包、KEY 文件、凭据、返回的私有知识片段或私有协议载荷。

## 下载、安装与开发验证

可先克隆源码并运行离线校验：

```text
git clone https://github.com/dongke141219/jl-private-knowledge-client.git
cd jl-private-knowledge-client
python -m unittest discover -s tests -v
```

在正式 GitHub 仓库已配置 Codex marketplace 元数据且生产网关已上线后，可执行：

```text
codex plugin marketplace add dongke141219/jl-private-knowledge-client --ref main
codex plugin marketplace list
codex plugin add jl-private-knowledge-client@<marketplace-name>
```

请不要盲目复制占位符，也不要在 `openai.yaml`、README、Git 历史或 issue 中填写访问凭据。首次连接由当前用户在正式身份认证流程中完成。

### 发布前校验

```text
python -m unittest discover -s tests -v
python <plugin-creator>/scripts/validate_plugin.py .
python <skill-creator>/scripts/quick_validate.py skills/jl-private-knowledge-client
```

## 安全反馈

若发现凭据暴露、客户信息泄漏、跨账号查询、过量知识返回或可重建完整知识库的问题，请使用 GitHub 仓库的私密安全报告渠道；不要在公开 issue 中粘贴凭据、源码或客户数据。

## License

[隐私说明](PRIVACY.md) · [使用条款](TERMS.md) · [MIT License](LICENSE)
