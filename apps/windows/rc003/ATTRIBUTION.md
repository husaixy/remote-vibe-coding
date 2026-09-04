# Remote Vibe Coding 归属与改动说明

本目录中的 Windows RC003 客户端基于以下 GPL-3.0-only 项目改造：

- 上游项目：[`nijez/open-voice-bridge`](https://github.com/nijez/open-voice-bridge)
- 上游 Windows 实现：`apps/windows/rc003/`
- 直接上游：[`miaomiaozii/windows-remote-mic-app`](https://github.com/miaomiaozii/windows-remote-mic-app)
- 本派生项目：Remote Vibe Coding（遥控语音编程）

上游项目已经提供了 RC003 的 Windows 参考实现，包括 WinRT BLE、ATVV 语音协议、
Windows Raw Input、SendInput、PortAudio 音频输出、Qt/QML 设置页、诊断、测试和
PyInstaller/Inno Setup 构建流程。Remote Vibe Coding 在 GPL-3.0-only 条件下保留
并适配这些能力，在上述项目基础上继续开发，并做了以下改动：

- 面向用户的应用标题、安装器和文档使用 `Remote Vibe Coding` 名称；
- 现阶段保留 `RemoteMicRC003.exe`、`RemoteMic` 配置目录、互斥锁和 `ovb_rc003`
  Python 包名，以兼容既有安装、设置和单实例行为；这些技术标识会在有迁移方案后再调整；
- 明确以遥控器快捷操作 Codex 和按住说话为后续产品方向；
- 适配本仓库现有的 `LICENSE.md`、`COPYRIGHT.md` 和第三方声明文件；
- 补充中文安装、配对、VB-CABLE 配置、按键映射和故障排查说明；
- 保留上游的失败关闭策略、隐私约束、跨平台协议测试和 Windows CI 校验；
- 明确声明当前候选版本已完成真实 RC003 硬件配对、逐键和语音链路验收；验收不能
  被自动构建或 CI 替代。

源码中仍保留 `ovb_rc003` 这一内部 Python 包名，以兼容现有安装并减少从上游同步修复时的差异；
它不是用户看到的应用名称。上游源码及其 GPL 许可适用于本目录中的派生代码，
本仓库根目录的 [`LICENSE.md`](../../../LICENSE.md) 是随源码发布的完整许可证。

## 其他参考来源

RC003 的 ATVV UUID、控制命令、IMA/DVI ADPCM 解码和 HID 映射事实见仓库根目录的
[`THIRD_PARTY_NOTICES.md`](../../../THIRD_PARTY_NOTICES.md)；本分支不依赖另一个平台
的实现文件。

VB-CABLE 是 VB-Audio 的独立第三方软件，不属于本项目的 GPL 代码。Windows 构建
脚本只在显式执行、哈希固定的步骤中获取官方安装包；应用不会静默安装或修改系统
默认音频设备。使用 VB-CABLE 前请阅读 Windows README 中的方向说明和许可证信息。
应用只会在用户明确确认后调用 Windows 的 `runas`/UAC 流程启动厂商安装器；另外，
用户可在“权限”页明确点击以启动短时、哈希校验的 RC001/RC003 HID 支持助手。
常驻设置、桥接和语音进程都不会以管理员权限运行。
