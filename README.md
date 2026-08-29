# JL Knowledge Base Skill

面向杰理（JL）SDK 开发者的 Codex Plugin：把需求、原理图、UI 说明和现有 SDK 一起交给 Codex，让它结合当前工程与共享开发经验，尽量直接完成代码修改、问题排查、编译验证和交付说明。

它不只是回答“这个功能在哪里”，更希望帮助你把一句客户需求真正落到工程里：先读当前项目，再定位实现点，修改必要代码，调用项目已有的构建方式验证，并明确告诉你哪些已经完成、哪些还需要上板或实机确认。

## 为什么值得使用

- **更快找到正确入口**：面对体量很大的 JL SDK，可结合芯片、SDK 版本、板级配置和相似问题经验，缩短反复搜索与试错时间。
- **从需求走到实际修改**：不仅给建议，还可以在你授权的项目中检查代码、修改文件、执行构建并整理结果。
- **能读懂配套资料**：可把需求文档、原理图、UI 交互稿、协议说明、报错日志和参考项目一起提供给 Codex，让它结合资料实现功能。
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

你可以把这些资料拖入 Codex 任务，或放到当前项目目录中：

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

资料越完整，Codex 越容易准确理解硬件连接、交互规则和验收标准。涉及硬件时，编译通过不等于实机一定通过，最终仍应按它给出的检查清单上板验证。

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

完成后可以要求 Codex 给出：

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

在用户首次明确同意后，完成过的实质功能和问题点可以被整理成**少量、结构化、脱敏**的经验候选。不会把完整源码、客户资料、原始日志、工程路径、固件、KEY、密码、令牌或私有协议内容直接上传为知识。

这些经验会带着 E1、E2、E3 等证据等级和适用范围保存。以后遇到相似需求时，Codex 只取回当前任务相关的少量片段，再以当前工程源码、真实编译和实机结果为准进行判断。随着真实完成和验证过的功能增加，可复用的问题点也会越来越丰富，因此后续项目通常能够更快定位、更少试错，而不是每次从零开始。

## 全新安装

目前只支持 Codex。不需要注册客户网页账号，不需要登录、申请、等待批准或领取个人凭据。

在终端运行：

```text
codex plugin marketplace add dongke141219/jl-knowledge-base-skill --ref main
codex plugin add jl-knowledge-base-skill@jl-knowledge
```

完成后彻底退出并重新打开 Codex，再新建一个任务使用。

也可以只运行第一条命令，重启 Codex 后在 **Plugins** 中找到 **JL Knowledge Base Skill** 并点击安装。

## 旧版本升级到最新版

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

## 免费与隐私

JL 知识服务免费提供；使用者自己的 Codex 账号、订阅和模型用量由使用者承担。

第一次需要贡献新经验时，Codex 会先说明脱敏范围并征求一次同意。不同意不会上传本地内容，也不影响继续使用当前 SDK 完成任务。源码、客户资料、完整日志、路径、固件、KEY、密码、令牌和私有协议内容不会作为知识贡献上传。

请只处理你有权使用的 SDK、文档和项目。知识经验用于辅助定位和决策，当前项目源码、真实编译以及实机测试结果始终具有更高优先级。

[隐私说明](PRIVACY.md) · [使用条款](TERMS.md) · [MIT License](LICENSE)

---

# JL Knowledge Base Skill

A Codex Plugin for Jieli (JL) SDK engineering. Give Codex an authorized SDK together with requirements, schematics, UI specifications, protocol documents, logs, or a reference project, and ask it to locate the implementation, modify the current project, run its existing build, and report the remaining hardware checks.

## Highlights

- Move from a customer requirement to concrete SDK changes instead of receiving only general advice.
- Use schematics, UI flows, protocol tables, error logs, and reference projects as task context.
- Work across keys, LEDs, ANC, microphones, audio, power and charging, Bluetooth/TWS, APP integration, UI, and build configuration.
- Reuse a few task-relevant, evidence-labelled JL engineering lessons while still treating the current source, real build, and hardware result as authoritative.
- Reduce repeated project explanation, blind searching, and trial-and-error. This may save time and model tokens, although the actual saving depends on the project and model.
- Turn completed work and diagnosed issues into small, sanitized, structured experience after one-time explicit consent, so future similar tasks can start from better evidence without uploading complete source code or customer material.

## Install

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

## Example

```text
Use $jl-sdk-engineer-core to implement this requirement in the current JL SDK.
Read the attached schematic, UI specification, and protocol document, inspect the current project,
modify the necessary files, run the project's existing Makefile, and report the completed changes,
build result, risks, and remaining hardware checks.
```

The service returns only a few task-relevant fragments. It does not replace project inspection, a real target build, or hardware verification.

[Privacy Notice](PRIVACY.md) · [Terms of Use](TERMS.md) · [MIT License](LICENSE)
