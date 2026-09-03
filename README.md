# JL Knowledge Base Skill

> **v0.8.0：先确认工程，再分类、查一次、做完后评估一次。** 不需要输入固定 Skill 名称或关键词；只有本地证据确认属于 JL 的项目才进入共享知识流程。

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

> **v0.7.1 暂时保持兼容。** 它访问共享服务时会收到 v0.8.0 升级提示，但因为旧包里没有升级器，这一次仍需按下文手工升级。v0.8.0 是第一版具备服务器版本核对和白名单自更新能力的客户端；离线旧包仍无法收到联网提示，本地 SDK 检查、修改和编译不受影响。

## 可以做什么

把用户有权使用的 JL SDK、需求和资料交给 Codex、Gemini CLI 或 ZCode，它可以结合当前工程与少量相关经验直接开展工作，例如：

- 根据自然语言需求定位并修改现有 JL SDK 项目，而不只是给一段分析。
- 结合原理图、UI 交互文档、协议表、参数表、错误现象、日志或参考工程完成实现。
- 处理按键、灯效、ANC/通透、麦克风、音频、电源充电、蓝牙/TWS、APP 对接、屏幕 UI 和构建配置等功能。
- 排查问题原因，做最小且完整的修复，并在条件允许时运行工程原有 Makefile 或构建入口。
- 清楚区分“已经修改”“真实编译通过”和“仍需实机验证”，避免把静态分析说成实机结论。
- 查询“某功能能否在指定芯片和 SDK 上实现、从哪里接入、有哪些边界和验证步骤”。关键词只帮助理解问题，不用于证明项目厂商；客户端会先从当前工程的目录、构建入口、芯片族和配置文件名识别，证据模糊时只追问一次。

确认后的固定流程是：先将需求分为“功能性需求”或“问题点”，再定位到产品、功能大项、能力、子功能/问题点与适用边界；随后只查询一次最相关的正式知识。命中且相关就作为参考，没有命中、不相关或服务不可用，AI 都会继续正常完成本地工作。

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

首次明确同意后，每个已确认的实质 JL 任务最多查询一次与当前问题相关的正式知识。AI 先完成实际任务，结束时再评估一次：只有形成了新的、可复用且有本地证据支持的工程结论，才整理至多一份小型、脱敏、结构化候选；候选经过审核后，才会进入同一个知识库的正式功能链供以后复用。

这不代表每句话或每次修改都会新增知识：普通闲聊、重复内容、没有可靠结论的猜测、共享知识片段原文都不会上传。同一结论会按规范化哈希去重；服务暂时失败只保留一份本地脱敏候选，不会卡住回答、循环重试或要求再次收口。

知识更完整后，相似任务可能少走弯路、减少重复搜索和反复解释，从而更快完成，也可能节省 AI Token；实际效果仍取决于当前工程、芯片、SDK、模型和资料完整度。

## 使用前准备

- 已安装并能正常使用 Codex、Gemini CLI 或 ZCode 其中一个客户端。
- 本机可执行 Python 3.10 或更高版本。Windows 可使用 `py -3`、`python` 或 `python3` 中任意一个有效命令；macOS/Linux 通常使用 `python3` 或 `python`。
- 只在自己有权使用的 SDK 和项目中工作。

安装或升级后请完全退出客户端、重新打开并新建任务。Codex 用户第一次使用前还应打开 `/hooks`，核对并信任本插件的四类生命周期 hook。

### 服务器版本核对与后续自动升级

v0.8.0 起，每次正常访问共享知识服务时，服务器都会同时返回最低兼容版本和最新版本。发现新版本后，AI 只能调用当前安装包内的 `scripts/client_update.py` 固定升级流程；服务器只给出版本号和固定动作编号，不能下发 PowerShell、Shell、路径、URL 或脚本正文让客户端执行。用户明确要求不自动升级时，AI 必须停止自动升级并只提示人工步骤。

- Codex：固定刷新已经配置的 `jl-knowledge` 市场、重装同名插件并用 JSON 列表核对版本。
- Gemini CLI：固定更新 `jl-knowledge-base-skill` 扩展并读取已安装 manifest 核对版本。
- ZCode：目前没有稳定的白名单命令行更新入口，因此只反馈“需要人工更新”，不会猜测或远程控制界面。

升级器最多立即执行一次；Codex 市场刷新失败时可用本机已有市场快照再安装一次。结果只把客户端类型、升级前后版本、阶段、成功/失败和固定错误码回报服务器，不上传命令输出、路径、设备名、账号或身份。失败后六小时内不会重复执行；未知问题留给服务端统计和后续发布修复，不会让 AI 自己运行任意修复命令。安装成功也要在当前任务结束后完全重启客户端并新建任务才会生效。

## Codex 全新安装（Windows 请整段复制）

Codex 桌面版自带的 `codex.exe` 不一定已经加入 Windows `PATH`。请打开 **PowerShell**，从下面两套方案中选择一套，并把该代码块**从第一行到最后一行一次性复制到同一个窗口执行**。不要只复制中间两行；新开 PowerShell 后也必须重新执行第一行。

### 方案 A：能正常访问 GitHub

```powershell
$codexExe = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $codexExe) { throw "没有找到 Codex 桌面版 codex.exe，请先安装或更新 Codex" }
& "$codexExe" plugin marketplace add dongke141219/jl-knowledge-base-skill --ref main
& "$codexExe" plugin add jl-knowledge-base-skill@jl-knowledge
& "$codexExe" plugin list
```

### 方案 B：中国大陆网络或 GitHub 连接被重置（推荐使用 Gitee）

这套命令会把本插件唯一的 GitHub 仓库地址重定向到内容一致的 Gitee 镜像，不影响其他 GitHub 仓库。

```powershell
$codexExe = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $codexExe) { throw "没有找到 Codex 桌面版 codex.exe，请先安装或更新 Codex" }
git config --global url."https://gitee.com/fofo123/jl-knowledge-base-skill.git".insteadOf "https://github.com/dongke141219/jl-knowledge-base-skill.git"
& "$codexExe" plugin marketplace add https://gitee.com/fofo123/jl-knowledge-base-skill.git --ref main
& "$codexExe" plugin add jl-knowledge-base-skill@jl-knowledge
& "$codexExe" plugin list
```

GitHub 和 Gitee 二选一，不要重复添加同名市场。

### 怎样判断 Codex 安装成功

最后的插件列表必须出现下面这一行，版本号可以高于示例：

```text
jl-knowledge-base-skill@jl-knowledge  installed, enabled  0.8.0
```

同时应看到：

```text
Added marketplace `jl-knowledge`
Added plugin `jl-knowledge-base-skill`
```

看到成功行后，必须把 Codex 的所有窗口彻底退出，再重新打开并新建任务。第一次访问共享知识时，应显示共同成长说明并要求用户本人准确输入“同意”。

### Codex 常见报错直接处理

- `codex 无法识别为 cmdlet`：桌面版 CLI 没有加入 PATH。不要直接输入 `codex`，重新完整执行上面的 PowerShell 代码块。
- `管道元素中的 & 后面表达式生成无效对象`：当前 PowerShell 窗口里没有 `$codexExe`。通常是只复制了后几行或打开了新窗口；从第一行重新整段执行。
- `RPC failed`、`curl 28`、`Connection was reset`、`10054`：GitHub 网络连接被重置，改用“方案 B：Gitee”。
- `marketplace jl-knowledge is not configured` 或 `plugin ... was not found`：前面的市场添加已经失败，后面的安装不会自动成功；先按对应方案重新添加市场，再安装插件。
- `plugin list` 输出很多内容：这是正常的。直接在输出末尾查找 `jl-knowledge-base-skill@jl-knowledge` 和 `installed, enabled`。
- 列表里仍显示 GitHub URL：这是插件清单记录的标准来源地址，不代表 Gitee 安装失败；只要状态为 `installed, enabled` 且存在本地安装目录即可。

### Codex 旧版本升级到最新版

请在同一个 PowerShell 窗口整段执行：

```powershell
$codexExe = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $codexExe) { throw "没有找到 Codex 桌面版 codex.exe，请先安装或更新 Codex" }
& "$codexExe" plugin marketplace upgrade jl-knowledge
& "$codexExe" plugin add jl-knowledge-base-skill@jl-knowledge
& "$codexExe" plugin list
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

到 **设置 → 插件 → 市场源** 刷新 `jl-knowledge`，再到已安装插件检查更新；更新并启用后必须新建会话。可在 **设置 → Hooks** 确认本插件的四类 hook 已随插件启用。

## 支持范围与联系作者

当前正式适配 **Codex、Gemini CLI 和 ZCode（GLM）**。如果希望在其他 AI 编程客户端使用，请通过 [GitHub Issues](https://github.com/dongke141219/jl-knowledge-base-skill/issues) 或 [Gitee Issues](https://gitee.com/fofo123/jl-knowledge-base-skill/issues) 联系作者，由作者完成兼容适配后再使用，避免安装成功但流程没有真正触发。

本工具不要求注册客户网页账号，不需要登录、申请、等待批准或领取个人凭据。用户使用自己的 AI 客户端、账号、模型、订阅和额度。

[隐私说明](PRIVACY.md) · [使用条款](TERMS.md) · [MIT License](LICENSE)

---

## English quick start

JL Knowledge Base Skill supports natural-language JL SDK implementation and diagnosis in Codex, Gemini CLI, and ZCode. It first confirms the current project from bounded local JL signatures; keywords alone do not activate shared access. It then classifies the feature or issue, performs at most one scoped query, finishes normal engineering work even on a miss or outage, and assesses once whether a genuinely new reusable local result should be contributed. No customer-platform registration, login, application, approval, or individual credential is required. On first shared use, the user must personally type the exact Chinese phrase `同意`.

The one shared knowledge base covers implementable capabilities, engineering implementation guides, product/chip/SDK applicability, boundaries, issue resolutions, and real build or hardware evidence. Sanitized reusable findings enter the candidate area of that same knowledge base and become searchable only after review. Complete source, SDKs, schematics, UI documents, firmware, raw logs, secrets, and identities are not uploaded.

Use the GitHub or Gitee commands above, restart the client, open an authorized JL SDK, and ask naturally.
