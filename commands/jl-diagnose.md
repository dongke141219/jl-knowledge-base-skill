---
description: 结合当前工程和少量共享经验排查并修复一个 JL SDK 问题
argument-hint: "<问题现象>"
skills: jl-knowledge-base-skill
---

排查并修复当前用户有权使用的杰理（JL）SDK 中的以下问题：

$ARGUMENTS

这是唯一的 JL 主工作流：先检查一次性同意状态。若尚未同意，必须先醒目展示“知识共同成长计划”，要求用户本人在输入框准确输入“同意”，并停止本次知识调用；不得替用户默认同意。未同意时可以继续使用本地 SDK，但不能创建、查询或提交共享知识任务。

若网关提示当前包已暂停或过期，停止共享调用并完整展示升级地址：https://github.com/dongke141219/jl-knowledge-base-skill 与 https://gitee.com/fofo123/jl-knowledge-base-skill；旧包完全离线时不能接收 NAS 主动更新。

先检查当前工程、用户提供的资料和日志，并尽量从本地工程识别芯片与 SDK 范围。查询与本问题直接相关的少量共享经验，以当前源码、真实编译和正确硬件验证为更高优先级证据。找到最可能原因后完成针对性修复，条件允许时运行项目原有构建入口。最后必须由当前任务的真实成功 MCP 回执得到唯一收口：查询有片段为“usage recorded”，查询为空为“server gap”，脱敏 solution 候选真实返回 `queued_for_review` 后替换为“solution candidate”。失败调用、本地排队或回答话术都不算。

如果当前工程和问题描述都不足以确定范围，再用大白话追问一个关键问题；不要发起空查询、通配查询或知识库遍历。
