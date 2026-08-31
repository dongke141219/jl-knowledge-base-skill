# JL Knowledge Base Skill — Codex、Gemini CLI 与 ZCode

> ## ⚠️ 使用前请先同意「知识共同成长计划」
>
> JL Knowledge Base Skill 是大家共同使用、共同完善的共享知识服务。
>
> 您在使用知识库解决 JL SDK 问题的同时，如果任务中形成了可复用的解决方法，系统会自动提取一份**脱敏的知识候选**上传。大家贡献的经验越多，知识库就越完整，今后遇到相同问题时就能更快找到答案、减少重复排查，也可能节省 AI Token。
>
> 系统不会上传或公开您的完整 SDK、完整源码、原理图、UI 文档、固件、原始日志、工程路径、客户身份、密码或密钥。只会整理与问题有关的结构化经验，例如：适用芯片和 SDK、问题现象、原因、解决方法以及验证情况。新内容会先进入候选知识库，审核通过后才会提供给其他用户。
>
> **使用共享知识库，就代表需要共同贡献可复用经验。只有大家一起贡献，大家才能共同拥有更全面、更准确、更好用的 JL 知识库。**
>
> 首次使用时，请在对话输入框中输入：**同意**
>
> **未输入“同意”，将无法访问 JL 共享知识库。**您仍可继续使用自己的 AI 客户端处理本地 SDK，但不会取得共享知识片段。
>
> **旧版 Skill 的共享知识访问已经暂停。**如果使用时看到升级提示，请直接前往 [GitHub](https://github.com/dongke141219/jl-knowledge-base-skill) 或 [Gitee](https://gitee.com/fofo123/jl-knowledge-base-skill) 获取最新版，重新启动客户端并新建任务后使用；本地 SDK 检查、修改和编译不受影响。
>
> 目前已适配 **Codex、Gemini CLI 和 ZCode**。若您希望在其他 AI 编程客户端中使用本 Skill，请通过 [GitHub Issues](https://github.com/dongke141219/jl-knowledge-base-skill/issues) 或 [Gitee Issues](https://gitee.com/fofo123/jl-knowledge-base-skill/issues) 联系作者，由作者完成兼容适配后再使用。

面向杰理（JL）SDK 开发者的 AI 编程插件，支持 Codex、Gemini CLI 和 ZCode（GLM）：把需求、原理图、UI 说明和现有 SDK 一起交给客户端，让它结合当前工程与共享开发经验，尽量直接完成代码修改、问题排查、编译验证和交付说明。

它不只是回答“这个功能在哪里”，更希望帮助你把一句客户需求真正落到工程里：先读当前项目并自动识别芯片和 SDK 范围，再定位实现点，修改必要代码，调用项目已有的构建方式验证，并明确告诉你哪些已经完成、哪些还需要上板或实机确认。

## 为什么值得使用

- **更快找到正确入口**：面对体量很大的 JL SDK，可结合芯片、SDK 版本、板级配置和相似问题经验，缩短反复搜索与试错时间。
- **从需求走到实际修改**：不仅给建议，还可以在你授权的项目中检查代码、修改文件、执行构建并整理结果。
- **Codex、Gemini CLI 和 ZCode 都能用**：三个客户端连接同一套受限共享经验，用户使用自己的客户端账号和模型额度，不需要客户网页账号。
- **能读懂配套资料**：可把需求文档、原理图、UI 交互稿、协议说明、报错日志和参考项目一起提供给当前客户端，让它结合资料实现功能。
- **经验带着可信边界**：共享经验会区分“已处理”“真实编译通过”和“实机验证通过”，避免把未经验证的结论说成最终答案。
- **遇到相似问题更省时间**：已经解决过的功能、踩过的坑、适用条件和验证结果可以沉淀成可复用经验，下次遇到相似项目时更快进入正确方向。
- **可能减少 Token 消耗**：知识服务只返回当前任务需要的少量片段，可减少重复解释背景、全工程盲目搜索和多轮试错带来的上下文消耗。实际节省量取决于任务复杂度、工程规模和所用模型。

## 可以做什么

### 1. 根据客户需求直接修改 JL SDK

- 按键短按、长按、组合键、按键映射和多击逻辑。
- LED 灯效、状态提示、开关机动画和充电状态显示。
- ANC、通透、MIC、EQ、音量、提示音和音频链路。
- 蓝牙连接、TWS 配对、左右耳同步、角色切换和断线重连。
- 低功耗、休眠唤醒、电池检测、电源管理和充电功能。
- APP 接入、设备控制、协议命令、状态同步和参数配置。
- 编译配置、宏开关、板级差异、功能移植和版本兼容问题。

### 2. 上传资料后结合当前工程实现功能

你可以把这些资料提供给 Codex、Gemini CLI 或 ZCode，也可以放到当前项目目录中：

- Word、PDF、Markdown、Excel 等需求或功能说明。
- 原理图 PDF、清晰截图、引脚表、器件说明和板级连接资料。
- UI 页面图、交互流程、状态跳转说明、图标和资源文件。
- APP／MCU／设备协议文档、命令表、字段说明和交互时序。
- 编译错误、运行日志、测试现象和复现步骤。
- 你有权使用的旧项目、参考工程或不同版本 SDK。

然后直接说明目标，例如：

```text
使用 $jl-sdk-engineer-core，结合我上传的原理图、UI 交互文档和当前 JL SDK，
完成充电仓 UI、电量显示和耳机状态同步功能。

请先核对板级引脚和现有代码，再修改必要文件，使用项目已有的 Makefile 编译，
最后列出已完成内容、编译结果和需要实机确认的步骤。
```

资料越完整，当前客户端越容易准确理解硬件连接、交互规则和验收标准。涉及硬件时，编译通过不等于实机一定通过，最终仍应按它给出的检查清单上板验证。

### 3. 排查问题并完成修复

```text
使用 $jl-sdk-engineer-core，结合 JL 知识库排查当前项目左右耳状态不同步的问题。
请检查现有实现和配置，找到原因并完成修复，使用项目自己的构建入口编译验证，
不要只给建议，要告诉我修改了什么以及还需要怎样进行实机测试。
```

可用于排查编译错误、功能无效、配置冲突、版本差异、左右耳不同步、功耗异常、协议交互异常、UI 状态错误等问题。

### 4. 参考已有项目移植功能

```text
使用 $jl-sdk-engineer-core，把参考工程中的三击切换 ANC 模式功能移植到当前 SDK。
先比较两个工程的芯片、SDK 版本、板级配置和事件流程，只移植当前项目真正需要的部分，
完成后做真实编译并说明风险与实机测试项。
```

### 5. 把交付结果说清楚

完成后可以要求当前客户端给出：

- 修改过的文件和每项修改的用途。
- 哪些需求已经实现，哪些只是完成了代码处理。
- 是否执行了真实编译，使用了哪个现有构建入口，结果是否通过。
- 还需要验证的按键、灯效、音频、连接、充电、功耗和异常场景。
- 如果失败，失败发生在哪一步、已确认什么、建议下一步检查什么。

## 为什么会越用越智能

JL SDK 中很多问题会重复出现，但不同芯片、SDK 版本、产品形态和板级配置又存在差异。单纯记住一段代码并不可靠，因此知识库沉淀的不是整套工程，而是经过整理的可复用经验，例如：

- 某类功能通常从哪里进入、涉及哪些模块和配置。
- 某个问题出现时应优先检查什么，以及曾经踩过哪些坑。
- 经验适用于什么产品、芯片、SDK 和功能范围。
- 当时真正做了哪些处理，是否通过真实编译或实机验证。
- 哪些方案失败过、失败边界是什么，避免下次重复走弯路。

在用户首次明确输入“同意”后，完成过的实质功能和问题点会被整理成**少量、结构化、脱敏**的经验候选。没有可靠解决结论时，只记录“知识缺口”，不会编造答案。不会把完整源码、客户资料、原始日志、工程路径、固件、KEY、密码、令牌或私有协议内容直接上传为知识。

这些新经验会先进入**候选知识库**，不会马上作为答案提供给其他用户。通过内部审核后才会合并到**正式共享知识库**。以后遇到相似需求时，Codex、Gemini CLI 或 ZCode 只取回当前任务相关的少量正式片段，再以当前工程源码、真实编译和实机结果为准进行判断。随着真实完成和验证过的功能增加，可复用的问题点也会越来越丰富，因此后续项目通常能够更快定位、更少试错，而不是每次从零开始。

## 安装与升级

支持 **Codex、Gemini CLI 和 ZCode**。不需要注册客户网页账号，不需要登录、申请、等待批准或领取个人凭据。

安装完成后的第一次知识任务会显示“知识共同成长计划”。请阅读说明，并由用户本人在对话输入框中输入 **同意**。客户端不得根据安装动作、历史消息或默认设置替用户同意；未输入“同意”时，服务器不会创建知识任务，也不会返回共享知识片段。

三种客户端共用的首次同意记录和脱敏候选队列需要本机已安装 **Python 3.10 或更高版本**，只使用 Python 标准库，不会额外安装依赖。Windows、macOS 或 Linux 上可用的命令可能是 `python`、`python3` 或 `py -3`，客户端会选取实际指向 Python 3.10+ 的一个。没有 Python 时仍可用自己的 AI 客户端处理本地 SDK，但共享知识访问和自动贡献不会启用；安装 Python 后请新建一个任务再输入“同意”。

### Codex 全新安装

在终端运行：

```text
codex plugin marketplace add dongke141219/jl-knowledge-base-skill --ref main
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

完成后彻底退出并重新打开 Codex，再新建一个任务使用。

也可以只运行第一条命令，重启 Codex 后在 **Plugins** 中找到 **JL Knowledge Base Skill** 并点击安装。

### Codex 旧版本升级到最新版

如果已经安装过 v0.3.1 或更高版本，在终端运行：

```text
codex plugin marketplace upgrade jl-knowledge
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

然后彻底退出并重新打开 Codex，**新建一个任务**再测试。旧任务可能仍然保留启动时加载的旧 Skill 和旧连接配置。

如果安装的是更早版本，插件名称仍显示为 `jl-private-knowledge-client`，或者升级后找不到新版，请执行一次干净更新：

```text
codex plugin remove jl-private-knowledge-client@jl-knowledge
codex plugin marketplace remove jl-knowledge
codex plugin marketplace add dongke141219/jl-knowledge-base-skill --ref main
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

某条删除命令提示“未安装”时可以继续执行后面的命令。完成后重启 Codex，并在新任务中使用 `$jl-sdk-engineer-core`。

### Gemini CLI 全新安装

请先安装 Gemini CLI 和 Git，然后在普通终端中运行：

```text
gemini extensions install https://github.com/dongke141219/jl-knowledge-base-skill --auto-update
```

安装命令需要在普通终端执行，不能在 Gemini CLI 的交互会话内执行。安装完成后退出并重新打开 Gemini CLI，在你有权使用的 JL SDK 目录中开始任务。

可在 Gemini CLI 中运行下面两条命令确认扩展和知识工具已经加载：

```text
/extensions list
/mcp
```

### Gemini CLI 更新

在普通终端中运行：

```text
gemini extensions update jl-knowledge-base-skill
```

更新后重新启动 Gemini CLI 会话。扩展也提供两个可选快捷命令：

```text
/jl:implement 把三击功能改为切换 ANC、通透和关闭
/jl:diagnose 左右耳状态不同步，帮我找到原因并修复
```

也可以直接说“帮我查下 ANC 为什么没效果”。如果当前打开的是完整 SDK，客户端会先从项目中识别芯片和版本，不要求用户每次手动填写芯片；只有项目和问题都没有足够范围时，才会用大白话追问一次。

### ZCode（GLM）全新安装

1. 打开 ZCode，进入 **设置 → 插件**。
2. 点击右上角 **创建 → 添加插件市场**。
3. 填入下面这个 GitHub 仓库地址并确认：

```text
https://github.com/dongke141219/jl-knowledge-base-skill
```

4. 在插件页面的 **个人** 分区找到 **JL Knowledge Base Skill**，点击 **安装** 并启用。
5. 新建一个 ZCode 任务，打开你有权使用的 JL SDK 目录后直接描述需求。

安装后可在 **设置 → MCP** 中看到插件提供的 JL 知识连接。日常使用不必记命令，也不必每次主动填写芯片，例如可以直接说：

```text
帮我查下这个项目 ANC 为什么没效果，找到原因后直接修复并编译验证。
```

ZCode 会先查看当前 SDK，尽量从工程中识别芯片和版本。只有当前目录不是完整 SDK、并且问题描述也不足以判断范围时，才会追问一个关键问题。

也可以使用两个快捷命令：

```text
/jl-implement 把三击功能改为循环切换 ANC、通透和关闭
/jl-diagnose 左右耳状态不同步，帮我找到原因并修复
```

### ZCode 旧版本升级

打开 **设置 → 插件 → 市场源**，刷新 `jl-knowledge` 市场，然后回到已安装插件执行更新。更新完成后新建一个任务再测试，旧任务可能仍保留启动时加载的旧 Skill 和连接配置。

## 推荐提问方式

为了更快得到可交付结果，建议一次说清楚：

1. 产品和芯片型号，以及大致 SDK 版本。
2. 当前现象与期望结果。
3. 需要参考的需求、原理图、UI、协议或旧工程。
4. 哪些文件或模块不能改。
5. 项目原有的编译方式和最终需要验证的硬件场景。

例如：

```text
使用 $jl-sdk-engineer-core 完成这个需求，不要只分析。
请阅读当前 SDK 和我上传的需求、原理图及 UI 文档，先确认现有实现和硬件连接，
再修改必要代码，使用项目原有 Makefile 做真实编译。
最后按“已修改、编译结果、风险、实机验证步骤”四部分告诉我结果。
```

Gemini CLI 和 ZCode 可以直接说：

```text
请结合 JL 知识库完成这个需求，不要只分析。
阅读当前 SDK 和我提供的需求、原理图及 UI 文档，自动识别芯片和版本，
修改必要代码，使用项目原有 Makefile 做真实编译，
最后告诉我已修改内容、编译结果、风险和实机验证步骤。
```

## 免费与隐私

JL 知识服务免费提供；使用者自己的 Codex、Gemini 或 ZCode/GLM 账号、订阅和模型用量由使用者承担。

第一次访问共享知识库时，当前客户端会先醒目说明共同贡献和脱敏范围，并要求用户本人输入“同意”。同意一次后，后续实质任务形成的脱敏知识候选会自动进入候选知识库，不再逐条打断确认；候选经过审核后才可能进入正式共享知识库。不同意不会上传本地内容，也不能访问共享知识库，但不影响用户用自己的客户端继续处理本地 SDK。源码、客户资料、完整日志、路径、固件、KEY、密码、令牌和私有协议内容不会作为知识贡献上传。

请只处理你有权使用的 SDK、文档和项目。知识经验用于辅助定位和决策，当前项目源码、真实编译以及实机测试结果始终具有更高优先级。

[隐私说明](PRIVACY.md) · [使用条款](TERMS.md) · [MIT License](LICENSE)

---

# JL Knowledge Base Skill — Codex, Gemini CLI & ZCode

> ## ⚠️ Agreement required before shared-knowledge access
>
> This is a community-growing knowledge service: users receive task-scoped JL experience and, after substantive work, automatically contribute only a small sanitized knowledge candidate. More verified contributions make future work faster and the shared coverage broader.
>
> Complete SDKs, source, schematics, UI documents, firmware, raw logs, project paths, customer identity, passwords, keys, credentials, and private payloads are not uploaded. New candidates stay in a review queue and are not served to other users until approved.
>
> On first use, the user must type the exact Chinese phrase **同意** in the conversation. Without it, the shared knowledge service cannot be accessed. Local SDK work in the user's own AI client remains available.
>
> **Shared-knowledge access from older Skill versions has been paused.** If an upgrade notice appears, download the latest version directly from [GitHub](https://github.com/dongke141219/jl-knowledge-base-skill) or [Gitee](https://gitee.com/fofo123/jl-knowledge-base-skill), restart the client, and begin a new task. Local SDK inspection, editing, and building remain available.
>
> Codex, Gemini CLI, and ZCode are currently supported. To use this Skill in another AI coding client, contact the author through [GitHub Issues](https://github.com/dongke141219/jl-knowledge-base-skill/issues) or [Gitee Issues](https://gitee.com/fofo123/jl-knowledge-base-skill/issues) so an official compatibility adaptation can be completed first.

An AI coding plugin for Jieli (JL) SDK engineering in Codex, Gemini CLI, and ZCode. Give the client an authorized SDK together with requirements, schematics, UI specifications, protocol documents, logs, or a reference project, and ask it to locate the implementation, modify the current project, run its existing build, and report the remaining hardware checks.

## Highlights

- Move from a customer requirement to concrete SDK changes instead of receiving only general advice.
- Use the same task-scoped shared JL experience from Codex, Gemini CLI, or ZCode with no customer-platform account.
- Use schematics, UI flows, protocol tables, error logs, and reference projects as task context.
- Work across keys, LEDs, ANC, microphones, audio, power and charging, Bluetooth/TWS, APP integration, UI, and build configuration.
- Reuse a few task-relevant, evidence-labelled JL engineering lessons while still treating the current source, real build, and hardware result as authoritative.
- Reduce repeated project explanation, blind searching, and trial-and-error. This may save time and model tokens, although the actual saving depends on the project and model.
- Turn completed work and diagnosed issues into small, sanitized, structured experience after one-time explicit consent, so future similar tasks can start from better evidence without uploading complete source code or customer material.

## Codex install

No customer-platform registration, login, application, approval, or individual credential is required.

```text
codex plugin marketplace add dongke141219/jl-knowledge-base-skill --ref main
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

Fully restart Codex and start a new task.

## Upgrade

For v0.3.1 or later:

```text
codex plugin marketplace upgrade jl-knowledge
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

For an older installation still named `jl-private-knowledge-client`:

```text
codex plugin remove jl-private-knowledge-client@jl-knowledge
codex plugin marketplace remove jl-knowledge
codex plugin marketplace add dongke141219/jl-knowledge-base-skill --ref main
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

Restart Codex and use a new task so the updated skills and connection are loaded.

## Gemini CLI install and update

```text
gemini extensions install https://github.com/dongke141219/jl-knowledge-base-skill --auto-update
```

Restart Gemini CLI, open an authorized JL SDK, and ask naturally. The extension can infer the chip and SDK scope from the current project; it asks one short clarification only when neither the project nor the request provides enough scope.

Optional shortcuts:

```text
/jl:implement <requirement>
/jl:diagnose <problem>
```

Update later from a normal terminal:

```text
gemini extensions update jl-knowledge-base-skill
```

## ZCode install and update

Open **Settings → Plugins → Create → Add plugin marketplace**, then enter:

```text
https://github.com/dongke141219/jl-knowledge-base-skill
```

Find **JL Knowledge Base Skill** under **Personal**, install and enable it, then start a new task in an authorized JL SDK. Ask naturally or use:

```text
/jl-implement <requirement>
/jl-diagnose <problem>
```

To update, refresh the `jl-knowledge` source under **Settings → Plugins → Marketplace Sources**, update the installed plugin, and start a new task.

## Example

```text
Use $jl-sdk-engineer-core to implement this requirement in the current JL SDK.
Read the attached schematic, UI specification, and protocol document, inspect the current project,
modify the necessary files, run the project's existing Makefile, and report the completed changes,
build result, risks, and remaining hardware checks.
```

In Gemini CLI or ZCode, the same request can be written without the dollar-prefixed skill name:

```text
Use the JL knowledge extension to implement this requirement in the current SDK.
Infer the chip and SDK version from the project, make the necessary changes,
run the existing Makefile, and report the build result and hardware checks.
```

The service returns only a few task-relevant fragments. It does not replace project inspection, a real target build, or hardware verification.

[Privacy Notice](PRIVACY.md) · [Terms of Use](TERMS.md) · [MIT License](LICENSE)
