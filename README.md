# 免费 JL SDK 知识库与 AI 工程助手

这是一个面向杰理（JL）SDK 开发者的 Codex Plugin。打开自己的 JL SDK，直接告诉 Codex 客户需要什么，它会结合当前项目和共享经验完成分析、修改与编译验证。

## 可以做什么

- 根据客户需求修改现有 JL SDK 项目。
- 帮助定位按键、灯效、ANC、MIC、音频、电源充电、蓝牙/TWS、APP 接入等功能。
- 结合相似项目经验排查编译错误和功能问题。
- 使用项目自己的 Makefile 或现有构建入口做真实编译。
- 清楚区分“已经修改”“编译通过”和“仍需实机验证”。

知识库只会给出当前任务相关的少量经验，并保留 E1、E2、E3 等可信等级，方便 Codex 判断哪些内容还需要在当前项目中确认。

## 安装

目前只支持 Codex。

先在终端运行：

```text
codex plugin marketplace add dongke141219/jl-private-knowledge-client --ref main
```

然后重启 Codex，在 **Plugins** 中找到 **JL SDK Knowledge & Engineer** 并安装。

不需要注册客户网页账号，不需要登录、申请、等待批准或领取个人凭据。公开服务开启时，安装后即可使用。

## 使用

在 Codex 中打开你有权使用的 JL SDK，然后直接说：

```text
使用 $jl-sdk-engineer-core，根据当前 SDK 完成以下需求：
1. 修改按键功能……
2. 修改灯效……
3. 接入 ANC……

请结合 JL 知识库中的相关经验，检查现有实现，修改必要文件，
使用项目自己的 Makefile 编译，并告诉我结果和还需要验证的内容。
```

排查问题可以说：

```text
使用 $jl-sdk-engineer-core，结合 JL 知识库排查当前项目左右耳同步失败的问题。
请找到原因、完成修复，并用 Makefile 编译验证。
```

## 免费与隐私

JL 知识服务免费提供；使用者自己的 Codex 账号、订阅和模型用量由使用者承担。

第一次需要贡献新经验时，Codex 会先说明脱敏范围并征求一次同意。不同意不会上传本地内容。源码、客户资料、完整日志、路径、固件、KEY、密码、令牌和私有协议内容不会作为知识贡献上传。

维护者可以统一开启或停止公开知识服务。停止后所有 GitHub 用户都无法取得共享知识，但 Plugin 仍可继续处理用户自己的本地 SDK。

[隐私说明](PRIVACY.md) · [使用条款](TERMS.md) · [MIT License](LICENSE)

---

# Free JL SDK Knowledge & AI Engineer

A Codex Plugin for working on Jieli (JL) SDK projects with task-relevant shared experience. It helps locate implementation points, modify the current project, diagnose issues, run the project's own build, and separate build results from remaining hardware checks.

## Install

```text
codex plugin marketplace add dongke141219/jl-private-knowledge-client --ref main
```

Restart Codex, open **Plugins**, and install **JL SDK Knowledge & Engineer**. No customer-platform registration, login, application, approval, or individual credential is required.

## Use

Open an authorized JL SDK in Codex and ask:

```text
Use $jl-sdk-engineer-core to implement this requirement in the current JL SDK.
Use relevant JL knowledge, run the project's own Makefile, and report the result
and the remaining hardware checks.
```

The shared service returns only a few task-relevant, evidence-labelled fragments. The maintainer may stop the public service for every GitHub user at once; local SDK work remains available.

[Privacy Notice](PRIVACY.md) · [Terms of Use](TERMS.md) · [MIT License](LICENSE)
