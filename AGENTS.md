# Remote Vibe Coding 开发规则

## 项目目标

- 正式产品名称为 **Remote Vibe Coding**，中文说明名为“遥控语音编程”。
- 本项目在 Windows 上把小米蓝牙遥控器 2 / 2 Pro（RC001 / RC003）变成 Codex 的便携按键与语音输入面板。
- 新功能必须服务于可见、可配置、可恢复的遥控器操作；不能依赖读取第三方应用私有数据、内部数据库或私有协议。

## Git 与上游

- 本仓库是独立 Git 工作库。保留 `origin` 指向 `miaomiaozii/windows-remote-mic-app` 作为直接上游；个人仓库使用单独 remote。
- 不改写上游历史。开始修改前检查 `git status`，按可独立审查的目的提交。
- 提交前运行 `git diff --check` 和相关测试；涉及桌面打包时运行 Windows 候选构建。
- 不提交 `.venv/`、`dist/`、`target/`、`node_modules/`、日志、诊断原始记录、真实设备标识、语音数据或第三方驱动安装包。

## 版本与提交管理

- 版本号遵循 SemVer。日常功能与修复先记录在 `apps/windows/rc003/CHANGELOG.md` 的 `Unreleased`；只有准备候选版或正式发布时才提升版本号并创建 tag。
- 发布改版时同步检查 `apps/windows/rc003/src/ovb_rc003/__init__.py`、`apps/windows/rc003/pyproject.toml` 和 `apps/windows/rc003/installer/RemoteMicRC003Setup.iss`，不得让包版本、应用版本和安装器版本无说明地漂移。
- 每个新增功能、修复或文档规则形成目的明确、可独立审查的提交；不要把无关改动混入同一提交。提交说明使用 `feat:`、`fix:`、`docs:`、`test:`、`chore:` 等前缀说明性质。
- 新功能完成后必须先更新测试与 `CHANGELOG.md`，执行相关验证和 `git diff --check`，再提交到当前功能分支；未经用户明确要求不推送、不发布、不改写历史。
- 候选版 tag 使用 `v<内部版本>-windows-rc003-candidate.<序号>`，正式版 tag 使用 `v<内部版本>-windows`；tag 必须指向已完成构建与验证的干净提交。

## 许可证与归属

- 项目继续按 `GPL-3.0-only` 发布，必须保留 `LICENSE.md`、`COPYRIGHT.md`、`THIRD_PARTY_NOTICES.md` 和 `apps/windows/rc003/ATTRIBUTION.md`。
- 复制或实质改编其他实现时，在归属说明中记录仓库、提交和模块。
- 用户可见名称使用 Remote Vibe Coding。为兼容现有安装，现阶段保留 `RemoteMicRC003.exe`、`RemoteMic` 配置目录、互斥锁和 `ovb_rc003` Python 包名。

## 架构与语音键

- Windows 客户端位于 `apps/windows/rc003`，Qt/QML 界面和 Python 平台实现保持清晰分层。
- 基础语音路径不得依赖管理员权限、Frida 注入或虚拟 HID 驱动；需要提权的修复只能由用户显式启动的独立 Helper 承载。
- 语音键只采用“按下开始、释放结束”的实时生命周期，不增加双击等待或长按阈值。
- 快速按下/释放、连续会话、断连和异常退出必须成对释放按键与音频状态。
- 原始语音键可能同时表现为 F5。任何拦截都必须限定到目标遥控器，不能全局屏蔽普通键盘 F5。

## 验证

- 安装依赖：`python -m pip install -r apps/windows/rc003/requirements-dev.txt`。
- 测试：在 `apps/windows/rc003` 下执行 `python -m unittest discover -s tests -t . -p 'test_*.py' -v`。
- 构建：执行 `apps/windows/rc003/build/build-candidate.ps1`。
- `passed` 只表示实际执行并观察通过；真实 RC001、RC003、Codex 和输入法联动必须分别真机验证，自动测试不能替代。
