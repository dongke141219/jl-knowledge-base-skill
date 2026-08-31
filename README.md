# JL Knowledge Base Skill

> **v0.7.1：直接用自然语言提问即可。** 不需要输入任何固定 Skill 名称或命令前缀；第一次同意后，后续普通 JL SDK 问题直接说需求就能使用。

官方下载入口（内容一致，任选一个即可）：

- [GitHub](https://github.com/dongke141219/jl-knowledge-base-skill)
- [Gitee](https://gitee.com/fofo123/jl-knowledge-base-skill)

请直接按下方对应客户端的小节安装；Codex、Gemini CLI 和 ZCode 的加载格式已分别适配，不要手工混装其他客户端的子包。

> ### ⚠️ 首次使用确认
>
> 使用本共享知识库，需要同意参加“知识共同成长计划”：系统会把任务中形成的可复用经验，整理成脱敏知识候选并上传审核。大家一起贡献，知识库才能越来越全面，后续遇到相同功能或问题时能更快找到答案、减少重复排查，也可能减少 Token 消耗。
>
> 这里只有一个共享知识库。它不只记录问题点，还包括：**能实现什么功能、工程实现指南、适用产品/芯片/SDK、使用边界、问题原因与解决方法、真实编译和实机验证证据**。新内容先进入**唯一共享知识库内的候选区**，审核通过后再进入正式区，并归入对应的完整功能链。
>
> 不会上传完整源码、SDK、原理图、UI 文档、固件、原始日志、密码、密钥、客户名称或个人身份信息。
>
> 如同意，请在对话输入框准确输入：**同意**
>
> 未输入“同意”，不能访问共享知识库；仍可让自己的 AI 客户端处理本地 SDK。

> **旧版 Skill 的共享知识访问已经暂停。** 请从 [GitHub](https://github.com/dongke141219/jl-knowledge-base-skill) 或 [Gitee](https://gitee.com/fofo123/jl-knowledge-base-skill) 升级到 v0.7.1，完全重启客户端并新建任务。离线旧包无法收到联网升级提示，但本地 SDK 检查、修改和编译不受影响。

## 可以做什么

把用户有权使用的 JL SDK、需求和资料交给 Codex、Gemini CLI 或 ZCode，它可以结合当前工程与少量相关经验直接开展工作，例如：

- 根据自然语言需求定位并修改现有 JL SDK 项目，而不只是给一段分析。
- 结合原理图、UI 交互文档、协议表、参数表、错误现象、日志或参考工程完成实现。
- 处理按键、灯效、ANC/通透、麦克风、音频、电源充电、蓝牙/TWS、APP 对接、屏幕 UI 和构建配置等功能。
- 排查问题原因，做最小且完整的修复，并在条件允许时运行工程原有 Makefile 或构建入口。
- 清楚区分“已经修改”“真实编译通过”和“仍需实机验证”，避免把静态分析说成实机结论。
- 查询“某功能能否在指定芯片和 SDK 上实现、从哪里接入、有哪些边界和验证步骤”。不要求用户每次手动填写芯片；客户端会先从当前工程识别，确实无法判断时才追问一个关键问题。

示例：

```text
根据这份原理图和 UI 文档，在当前 JL SDK 实现三击切换 ANC、通透和关闭；
使用工程原有构建方式编译，并告诉我已完成内容、风险和还要做的实机验证。
```

也可以直接说：

```text
帮我查一下这个 JL 耳机的 ANC 切换为什么无效，找到原因后直接修复并编译。
```

## 为什么会越用越智能

首次明确同意后，每个实质 JL 任务都会先查询与当前问题相关的正式知识。任务如果产生了可复用的实现、修复、诊断、编译结果或实机证据，客户端会整理一份小型、脱敏、结构化候选；候选经过审核后，才会进入同一个知识库的正式功能链供以后复用。

这不代表每句话都会新增一条知识：普通闲聊、重复内容、没有可靠结论的猜测不会冒充正式知识。纯查询任务可以记录本次命中或明确缺口；发生代码/配置修改、真实构建或形成可复用结论后，则必须提交与最新成果对应的脱敏候选。这样才能让增长有内容、有范围、有证据，而不是简单堆积回答文字。

知识更完整后，相似任务可能少走弯路、减少重复搜索和反复解释，从而更快完成，也可能节省 AI Token；实际效果仍取决于当前工程、芯片、SDK、模型和资料完整度。

## 使用前准备

- 已安装并能正常使用 Codex、Gemini CLI 或 ZCode 其中一个客户端。
- 本机可执行 Python 3.10 或更高版本。Windows 可使用 `py -3`、`python` 或 `python3` 中任意一个有效命令；macOS/Linux 通常使用 `python3` 或 `python`。
- 只在自己有权使用的 SDK 和项目中工作。

安装或升级后请完全退出客户端、重新打开并新建任务。Codex 用户第一次使用前还应打开 `/hooks`，核对并信任本插件的三个生命周期 hook。

## Codex 全新安装

GitHub：

```text
codex plugin marketplace add dongke141219/jl-knowledge-base-skill --ref main
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

Gitee：

```text
codex plugin marketplace add https://gitee.com/fofo123/jl-knowledge-base-skill.git --ref main
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

GitHub 和 Gitee 二选一，不要重复添加同名市场。

### Codex 旧版本升级到最新版

```text
codex plugin marketplace upgrade jl-knowledge
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

如果旧包还叫 `jl-private-knowledge-client`：

```text
codex plugin remove jl-private-knowledge-client@jl-knowledge
codex plugin marketplace remove jl-knowledge
```

然后按上面的 GitHub 或 Gitee 全新安装步骤重新安装。

## Gemini CLI 全新安装

GitHub 支持直接安装并开启自动更新：

```text
gemini extensions install https://github.com/dongke141219/jl-knowledge-base-skill --auto-update
```

GitHub 版手动升级：

```text
gemini extensions update jl-knowledge-base-skill
```

Gemini CLI 当前不把 Gitee 地址作为官方远程安装来源。使用 Gitee 时，先下载或克隆到本机，再按本地目录安装：

```text
git clone https://gitee.com/fofo123/jl-knowledge-base-skill.git
gemini extensions install <刚下载的 jl-knowledge-base-skill 本地目录>
```

Gitee 本地安装版升级：

```text
git -C <刚下载的 jl-knowledge-base-skill 本地目录> pull
gemini extensions update jl-knowledge-base-skill
```

重启 Gemini CLI 后直接提问。可选快捷命令：

```text
/jl:implement <功能需求>
/jl:diagnose <问题现象>
```

## ZCode（GLM）全新安装

打开 **设置 → 插件 → 创建 → 添加插件市场**，填入以下任意一个地址：

```text
https://github.com/dongke141219/jl-knowledge-base-skill
```

或：

```text
https://gitee.com/fofo123/jl-knowledge-base-skill.git
```

在“个人”区域找到 **JL Knowledge Base Skill**，安装并启用。新建会话后可以直接自然语言提问，也可以使用：

```text
/jl-implement <功能需求>
/jl-diagnose <问题现象>
```

### ZCode 旧版本升级

到 **设置 → 插件 → 市场源** 刷新 `jl-knowledge`，再到已安装插件检查更新；更新并启用后必须新建会话。可在 **设置 → Hooks** 确认本插件的三个 hook 已随插件启用。

## 支持范围与联系作者

当前正式适配 **Codex、Gemini CLI 和 ZCode（GLM）**。如果希望在其他 AI 编程客户端使用，请通过 [GitHub Issues](https://github.com/dongke141219/jl-knowledge-base-skill/issues) 或 [Gitee Issues](https://gitee.com/fofo123/jl-knowledge-base-skill/issues) 联系作者，由作者完成兼容适配后再使用，避免安装成功但流程没有真正触发。

本工具不要求注册客户网页账号，不需要登录、申请、等待批准或领取个人凭据。用户使用自己的 AI 客户端、账号、模型、订阅和额度。

[隐私说明](PRIVACY.md) · [使用条款](TERMS.md) · [MIT License](LICENSE)

---

## English quick start

JL Knowledge Base Skill supports natural-language JL SDK implementation and diagnosis in Codex, Gemini CLI, and ZCode. No customer-platform registration, login, application, approval, or individual credential is required. On first shared use, the user must personally type the exact Chinese phrase `同意`; afterwards, normal JL questions can use the shared workflow without repeating a Skill name.

The one shared knowledge base covers implementable capabilities, engineering implementation guides, product/chip/SDK applicability, boundaries, issue resolutions, and real build or hardware evidence. Sanitized reusable findings enter the candidate area of that same knowledge base and become searchable only after review. Complete source, SDKs, schematics, UI documents, firmware, raw logs, secrets, and identities are not uploaded.

Use the GitHub or Gitee commands above, restart the client, open an authorized JL SDK, and ask naturally.
