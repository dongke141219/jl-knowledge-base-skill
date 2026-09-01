【重要更新｜v0.7.1】

JL Knowledge Base Skill 现在可以直接用自然语言提问。不需要输入任何固定 Skill 名称，也不需要每次加 `$jl-knowledge-base-skill` 之类的命令。第一次同意知识共同成长计划后，以后打开自己有权使用的 JL SDK，直接说需求即可。

官方下载地址（内容一致，任选一个）：

- GitHub：https://github.com/dongke141219/jl-knowledge-base-skill
- Gitee：https://gitee.com/fofo123/jl-knowledge-base-skill

## 首次使用必须确认

使用本共享知识库，需要同意参加“知识共同成长计划”：系统会把任务中形成的可复用经验，整理成脱敏知识候选并上传审核。大家一起贡献，知识库才能越来越全面。以后遇到相同功能或问题时，可以更快找到答案、减少重复排查，也可能减少 AI Token 消耗。

这里只维护一个共享知识库。它不只记录问题点，还包括：能实现什么功能、工程实现指南、适用产品/芯片/SDK、使用边界、问题原因与解决方法、真实编译和实机验证证据。新内容会先进入唯一共享知识库里的候选区，审核通过后再进入正式区，并归入对应的完整功能链。

不会上传完整源码、完整 SDK、原理图、UI 文档、固件、原始日志、密码、密钥、客户名称或个人身份信息。

首次使用时，请在对话输入框准确输入：**同意**

未输入“同意”，不能访问共享知识库；但仍可以让自己的 AI 客户端处理本地 SDK。

## 旧版本请升级

旧版 Skill 的共享知识访问已经暂停。请从 GitHub 或 Gitee 升级到 v0.7.1，完全退出并重新打开客户端，然后新建任务。离线旧包无法主动收到联网升级提示，但本地 SDK 检查、修改和编译不受影响。

## 可以做什么

把自己有权使用的 JL SDK、需求和资料交给 Codex、Gemini CLI 或 ZCode，它可以结合当前工程和少量任务相关经验直接开展工作，例如：

- 根据自然语言需求定位并修改现有 JL SDK 项目，而不只是给分析建议。
- 结合原理图、UI 交互文档、协议表、参数表、错误现象、日志或参考工程完成实现。
- 处理按键、灯效、ANC/通透、麦克风、音频、电源充电、蓝牙/TWS、APP 对接、屏幕 UI 和构建配置等功能。
- 排查问题原因，完成最小且完整的修复，并在条件允许时运行工程原有 Makefile 或构建入口。
- 清楚区分“已经修改”“真实编译通过”和“仍需实机验证”。
- 查询某功能能否在指定芯片和 SDK 上实现、从哪里接入、有哪些边界和验证步骤。

客户端会先从当前工程识别芯片和 SDK，确实无法判断时才追问一个关键问题。

推荐提问：

```text
根据这份原理图和 UI 文档，在当前 JL SDK 实现三击切换 ANC、通透和关闭；
使用工程原有构建方式编译，并告诉我已完成内容、风险和还要做的实机验证。
```

也可以直接说：

```text
帮我查一下这个 JL 耳机的 ANC 切换为什么无效，找到原因后直接修复并编译。
```

## 为什么会越用越智能

第一次明确同意后，每个实质 JL 任务都会先查询与当前问题相关的正式知识。任务如果产生了可复用的实现、修复、诊断、编译结果或实机证据，客户端会整理一份小型、脱敏、结构化候选。候选经过审核后，才会进入同一个知识库的正式功能链，供以后遇到相似问题时复用。

普通闲聊、重复内容和没有可靠结论的猜测不会冒充正式知识。纯查询任务可以记录本次知识命中或明确缺口；发生代码或配置修改、真实构建，或者形成可复用结论后，则必须提交与最新成果对应的脱敏候选。

知识更完整以后，相似任务可能少走弯路，减少重复搜索和反复解释，从而更快完成，也可能节省 AI Token。

## 安装前准备

- 已安装并能正常使用 Codex、Gemini CLI 或 ZCode。
- 本机可以运行 Python 3.10 或更高版本。
- 只在自己有权使用的 SDK 和项目中工作。
- 安装或升级后，完全退出客户端，重新打开并新建任务。

## Codex 全新安装：Windows 请整段复制

Codex 桌面版自带的 `codex.exe` 不一定已经加入 Windows PATH。请打开 PowerShell，从下面两套方案中选择一套，并把代码块从第一行到最后一行一次性复制到同一个窗口执行。不要只复制中间几行；新开 PowerShell 后也必须重新执行第一行。

### 方案 A：能正常访问 GitHub

```powershell
$codexExe = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $codexExe) { throw "没有找到 Codex 桌面版 codex.exe，请先安装或更新 Codex" }
& "$codexExe" plugin marketplace add dongke141219/jl-knowledge-base-skill --ref main
& "$codexExe" plugin add jl-knowledge-base-skill@jl-knowledge
& "$codexExe" plugin list
```

### 方案 B：中国大陆网络或 GitHub 连接被重置，改走 Gitee

下面的重定向只针对本插件的唯一仓库，不影响其他 GitHub 仓库。

```powershell
$codexExe = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $codexExe) { throw "没有找到 Codex 桌面版 codex.exe，请先安装或更新 Codex" }
git config --global url."https://gitee.com/fofo123/jl-knowledge-base-skill.git".insteadOf "https://github.com/dongke141219/jl-knowledge-base-skill.git"
& "$codexExe" plugin marketplace add https://gitee.com/fofo123/jl-knowledge-base-skill.git --ref main
& "$codexExe" plugin add jl-knowledge-base-skill@jl-knowledge
& "$codexExe" plugin list
```

GitHub 和 Gitee 二选一，不要重复添加同名市场。

## 怎样判断 Codex 安装成功

最后的插件列表必须出现下面这一行，版本号可以高于示例：

```text
jl-knowledge-base-skill@jl-knowledge  installed, enabled  0.7.1
```

同时应看到：

```text
Added marketplace `jl-knowledge`
Added plugin `jl-knowledge-base-skill`
```

看到成功行后，必须把 Codex 的所有窗口彻底退出，再重新打开并新建任务。第一次访问共享知识时，应显示共同成长说明并要求用户本人准确输入“同意”。第一次使用前还应打开 `/hooks`，核对并信任本插件的三个生命周期 hook。

## Codex 常见报错直接处理

- `codex 无法识别为 cmdlet`：桌面版 CLI 没有加入 PATH。不要直接输入 `codex`，重新完整执行上面的 PowerShell 代码块。
- `管道元素中的 & 后面表达式生成无效对象`：当前 PowerShell 窗口里没有 `$codexExe`。通常是只复制了后几行或打开了新窗口；从第一行重新整段执行。
- `RPC failed`、`curl 28`、`Connection was reset`、`10054`：GitHub 网络连接被重置，改用“方案 B：Gitee”。
- `marketplace jl-knowledge is not configured` 或 `plugin ... was not found`：前面的市场添加已经失败，后面的安装不会自动成功；先重新添加市场，再安装插件。
- `plugin list` 输出很多内容：这是正常的，直接在输出末尾查找 `jl-knowledge-base-skill@jl-knowledge` 和 `installed, enabled`。
- 列表里仍显示 GitHub URL：这是插件清单记录的标准来源地址，不代表 Gitee 安装失败；状态为 `installed, enabled` 就算安装成功。

## Codex 旧版本升级

请在同一个 PowerShell 窗口整段执行：

```powershell
$codexExe = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $codexExe) { throw "没有找到 Codex 桌面版 codex.exe，请先安装或更新 Codex" }
& "$codexExe" plugin marketplace upgrade jl-knowledge
& "$codexExe" plugin add jl-knowledge-base-skill@jl-knowledge
& "$codexExe" plugin list
```

如果旧包还叫 `jl-private-knowledge-client`，先执行：

```powershell
& "$codexExe" plugin remove jl-private-knowledge-client@jl-knowledge
& "$codexExe" plugin marketplace remove jl-knowledge
```

然后按全新安装步骤重新安装。

## Gemini CLI 全新安装

GitHub：

```text
gemini extensions install https://github.com/dongke141219/jl-knowledge-base-skill --auto-update
```

手动升级：

```text
gemini extensions update jl-knowledge-base-skill
```

Gitee 版先下载到本机再安装：

```text
git clone https://gitee.com/fofo123/jl-knowledge-base-skill.git
gemini extensions install <刚下载的 jl-knowledge-base-skill 本地目录>
```

重新打开 Gemini CLI 后直接自然语言提问即可。可选快捷命令：

```text
/jl:implement <功能需求>
/jl:diagnose <问题现象>
```

## ZCode（GLM）安装

打开：设置 → 插件 → 创建 → 添加插件市场

填入以下任意一个地址：

```text
https://github.com/dongke141219/jl-knowledge-base-skill
```

或：

```text
https://gitee.com/fofo123/jl-knowledge-base-skill.git
```

在“个人”区域找到 JL Knowledge Base Skill，安装并启用。新建会话后可以直接自然语言提问。

ZCode 旧版本升级时，到“设置 → 插件 → 市场源”刷新 `jl-knowledge`，再到已安装插件检查更新；更新并启用后必须新建会话。可在“设置 → Hooks”确认本插件的三个 hook 已随插件启用。

## 支持范围与联系作者

当前正式适配：Codex、Gemini CLI、ZCode（GLM）。

如果希望在其他 AI 编程客户端使用，请通过 GitHub Issues 或 Gitee Issues 联系作者，由作者完成兼容适配后再使用，避免看似安装成功、实际流程没有触发。

- GitHub Issues：https://github.com/dongke141219/jl-knowledge-base-skill/issues
- Gitee Issues：https://gitee.com/fofo123/jl-knowledge-base-skill/issues

本工具不要求注册客户网页账号，不需要登录、申请、等待批准或领取个人凭据。每位用户使用自己的 AI 客户端、账号、模型、订阅和额度。

当前版本：v0.7.1
