# Remote Vibe Coding

**Remote Vibe Coding（遥控语音编程）** 是面向 Windows 的遥控器交互工具。它把小米蓝牙遥控器 2 / 2 Pro（RC001 / RC003）的按键和语音转换成 Windows 能识别的输入，让用户离开键盘时也能快速唤起语音输入、操作 Codex，并完成常用的 vibe coding 流程。

本项目派生自 [`miaomiaozii/windows-remote-mic-app`](https://github.com/miaomiaozii/windows-remote-mic-app)，继续采用 GPL-3.0-only 开源。当前版本保留并扩展其 Windows 蓝牙、按键映射和 ATVV 语音桥接能力；macOS 应用、Swift 工程和 macOS 发布资源不属于本仓库。

## 项目来源

- **直接拉取和持续同步的上游项目**：[`miaomiaozii/windows-remote-mic-app`](https://github.com/miaomiaozii/windows-remote-mic-app)。本仓库保留其 Git 历史、GPL-3.0-only 许可证和来源说明。
- **更早的原始项目**：[`HD838A/remote-mic-app`](https://github.com/HD838A/remote-mic-app)，最初用于把小米蓝牙遥控器 2 Pro / RC003 作为 macOS 语音输入设备。
- **当前二次开发仓库**：[`husaixy/remote-vibe-coding`](https://github.com/husaixy/remote-vibe-coding)。目前集中维护 Windows 客户端，不继续维护原项目的 macOS / Swift 工程。

## 我们做了哪些二次开发

在上游 Windows 蓝牙、ATVV 语音和按键桥接基础上，本项目完成了以下扩展：

- 将产品定位和界面统一为 **Remote Vibe Coding（遥控语音编程）**，增加新的应用图标、桌面快捷方式，以及极简扁平化的 PySide6 / Qt Quick 设置界面；
- 增加 RC001 与 RC003 的设备选择、配对诊断、真实按键检测、权限修复、日志入口和“保存并重启桥接”；
- 增加单击、双击、长按三种动作，并提供可视化映射、恢复默认值和运行时热加载；
- 增加 Codex 窗口唤醒、聚焦输入框、收起窗口以及 **Codex Micro 风格预设**；
- Codex 预设支持切换最近会话、调节推理强度、发送消息、批准/拒绝请求、切换侧边栏、搜索会话、Fork、新建会话以及 Fast / Plan 模式；
- 修复普通按键双触发、遥控器 F5 泄漏、蓝牙重连后 HID 未恢复、语音按键残留，以及桥接运行时电脑键盘方向键松开延迟等问题；
- 改进 VB-CABLE 音频路由、语音增益和重采样，并补充 PyInstaller 便携构建、Inno Setup 安装器、测试与完整操作文档。

所有 Codex 联动都使用 Windows 公共 API 和用户在 Codex 中主动设置的键盘快捷键；程序不会读取或修改 Codex 的私有数据库、内部配置或私有协议。

## 实现效果

完成配置后，可以把小米遥控器作为一块便携 Codex 控制面板：长按麦克风键说话、松开结束；用主页键唤醒并聚焦 Codex；用上下键切换最近会话；用音量键改变推理强度；用确认、返回、菜单、TV 和电源键完成发送、批准/拒绝、会话管理以及 Fast / Plan 切换。标准映射仍可用于 Windows 方向、音量、应用切换和媒体控制，用户可以随时修改或恢复。

当前版本已在真实 RC001 / RC003 上验证蓝牙连接、普通按键和 ATVV 语音链路。Codex 命令是否生效，还取决于本机 Codex 版本是否提供对应命令，以及用户是否完成下一节的快捷键绑定。

Windows 客户端位于 [`apps/windows/rc003`](apps/windows/rc003/README.md)，提供：

- WinRT BLE 连接与 ATVV 语音解码；
- Windows Raw Input + Frida HID 旁路按键监听，SendInput 按键映射；
- 语音输出到用户明确选择的音频端点（配合虚拟声卡供输入法识别）；
- PySide6/Qt Quick 设置窗口、诊断和 PyInstaller/Inno Setup 构建。

当前版本是**已通过真实硬件验收的源码/构建候选**：已在真实 RC003 遥控器上完成
配对、逐键与语音链路验收（方向/OK/Home/Menu/TV/Power/返回/音量± 全部单次触发，
麦克风键可启动豆包输入法并识别语音）。产物未签名；CI 和自动构建不能替代真实
硬件验收。

## 项目方向

Remote Vibe Coding 将遥控器作为 Codex 的便携输入面板，优先建设以下能力：

- 按住语音键说话，松开后结束，把语音可靠地送入输入法或 Codex 输入框；
- 将方向、确认、返回和音量等实体键映射为 Codex 常用操作；
- 提供可见、可修改、可恢复默认值的按键方案；
- 只通过 Windows 公共 API、公开快捷键和用户可见界面协作，不读取第三方应用私有数据。

现有功能和真机验收结论仍以本文及 Windows 客户端文档明确列出的范围为准；路线中的新功能会在完成代码、Windows 构建和真实遥控器验证后标记为可用。

## RC001 兼容适配

小米蓝牙遥控器 2（RC001）现已加入同一 Windows 客户端。Windows 实机显示
RC001 与 RC003 使用相同的蓝牙 HID 身份（VID `0x2717` / PID `0x32B8`）、
相同的配对名称“小米蓝牙语音遥控器”和相同的 `AB5E0001…` ATVV 语音服务，
因此两款设备共用同一套按键、语音解码和音频输出后端。设置页中可单独选择
“小米蓝牙遥控器 2（RC001）”；原有 RC003 配置不迁移、不重命名。

当前适配已在一只 Model Number 明确上报为 `RC001` 的真机上验证：设备返回
ATVV v1.0、16 kHz、120-byte frame，语音键触发 `MIC_OPEN` 后成功收到并解码
PCM。该结论不依赖相同外观或 VID/PID 推断；更多固件版本和长时间稳定性仍建议
继续复核。

## 截图

![连接设置页](docs/screenshots/settings-connection.png)

![按键映射页](docs/screenshots/settings-buttons.png)

> 截图在 Windows 11 + RC003 实测环境拍摄；如与你的系统主题/分辨率不同属正常差异。

## 下载与安装

当前二次开发版以预发布候选版 [v0.2.0-windows-rc003-candidate.1](https://github.com/husaixy/remote-vibe-coding/releases/tag/v0.2.0-windows-rc003-candidate.1) 提供，也可在[当前仓库 Releases](https://github.com/husaixy/remote-vibe-coding/releases)查看后续版本。上游历史正式版 [v0.1.0-windows](https://github.com/miaomiaozii/windows-remote-mic-app/releases/tag/v0.1.0-windows) 不包含本仓库新增的极简 UI、品牌图标、键盘方向键修复和 Codex Micro 预设。

从 Release 页面 Assets 下载，二选一：

| 资产 | 适用场景 |
| --- | --- |
| `RemoteMicRC003Setup-0.2.0-rc.1-unsigned.exe` | 推荐，安装到开始菜单/桌面并创建快捷方式 |
| `RemoteMicRC003-0.2.0-rc.1-portable-unsigned.zip` | 免安装，解压到任意目录直接运行 |

两个都未签名，Windows SmartScreen 会提示，点“更多信息 → 仍要运行”即可。
建议同时下载 `SHA256SUMS.txt` 校验文件哈希。

## 快速开始（安装版）

1. 下载 `RemoteMicRC003Setup-...exe` 并运行，一路“下一步”完成安装；
2. 在 Windows **设置 → 蓝牙和设备**中配对 RC001 或 RC003 遥控器；
3. 安装并配置 VB-CABLE，确认播放端存在 `CABLE Input`、录音端存在 `CABLE Output`；
4. 打开“Remote Vibe Coding 设置”，在连接页选择实际型号和 `CABLE Input` 输出端点；
5. 根据使用的输入法选择语音快捷键。当前真机方案通常使用长按模式 `Right Alt`，但应先用普通键盘验证输入法确实响应；
6. 完成下面的 Codex 快捷键绑定；
7. 在“按键映射”页点击“应用 Codex 预设”，检查映射后点击“保存映射”；
8. 回到连接页点击“保存并重启桥接”，再依次测试普通按键、Codex 命令和麦克风语音。

### 使用 Codex 前：手动绑定聚焦快捷键

> **必须先配置 Codex 快捷键。** 本程序不会自动修改 Codex 设置。没有完成绑定时，遥控器可能能够唤醒 Codex，但切换会话、推理强度、发送和批准等动作不会生效。

1. 打开 Codex 的 **设置 → 键盘快捷键（Keyboard Shortcuts）**。
2. 搜索 **聚焦主聊天 / Focus main chat**，将其绑定为 **`Ctrl+Alt+Shift+F12`** 并保存。这是本项目使用的组合键，不是 Codex 的默认快捷键。
3. 在已有可输入的 Codex 对话中，先用键盘按该组合键，输入几个字，确认文字进入对话输入框。
4. 如果使用 Codex Micro 风格预设，继续绑定下表中的命令：

| Codex 键盘快捷键命令 | 需要绑定为 |
| --- | --- |
| Previous recently viewed chat | `Ctrl+Alt+Shift+F1` |
| Next recently viewed chat | `Ctrl+Alt+Shift+F2` |
| Decrease reasoning effort | `Ctrl+Alt+Shift+F3` |
| Increase reasoning effort | `Ctrl+Alt+Shift+F4` |
| Approve request | `Ctrl+Alt+Shift+F5` |
| Decline request | `Ctrl+Alt+Shift+F6` |
| Toggle sidebar | `Ctrl+Alt+Shift+F7` |
| Switch chat… | `Ctrl+Alt+Shift+F8` |
| Fork chat | `Ctrl+Alt+Shift+F9` |
| New chat | `Ctrl+Alt+Shift+F10` |
| Toggle Fast mode | `Ctrl+Alt+Shift+F11` |
| Toggle Plan mode | `Ctrl+Alt+Shift+P` |
| Send message | `Ctrl+Alt+Shift+Enter` |

5. 逐项用普通键盘测试这些组合键；存在冲突时，先解除其他命令或软件占用，再保持 Codex 与 Remote Vibe Coding 两端一致。
6. 在 Remote Vibe Coding 的“按键映射”中应用 Codex 预设并保存。升级会保留旧映射，不会强制覆盖已有配置。
7. 关闭设置窗口后测试：Codex 在前台时短按主页键收起；切到其他应用后长按主页键约 0.55 秒唤醒并聚焦，再测试上下、音量、确认等按键。

`Focus main chat` 是其余 Codex 动作的前置绑定：程序会先唤醒并聚焦 Codex，再发送具体命令。不同 Codex 版本或界面语言可能显示不同名称；如果某个命令在本机不存在，该动作暂时不可用，其他已绑定动作不受影响。

如果只能唤醒窗口、无法输入文字，先检查第 2、3 步；如果普通按键也全部无效，按客户端文档检查按键通道。
完整说明见 [主页键控制 Codex](apps/windows/rc003/README.md#主页键控制-codex)。

### Codex Micro 风格预设

在“按键映射”页点击 **应用 Codex 预设**，可以一次载入面向 Codex 的遥控器布局。
这一步只更新页面中的待保存映射；确认无误后仍需点击“保存映射”。预设不会读取或
修改 Codex 的私有配置，首次使用需要在 Codex 的 **设置 → 键盘快捷键** 中手动绑定
命令。完整的按键分配与快捷键表见
[Codex Micro 风格预设](apps/windows/rc003/README.md#codex-micro-风格预设)。

### 其他使用注意事项

- **语音需要完整音频链路**：遥控器语音经 ATVV 解码后输出到选定播放端点；输入法应从对应的虚拟录音端读取。只连接蓝牙而不配置音频端点，普通按键可能正常但语音不会进入输入法。
- **语音不直接调用 Codex API**：麦克风音频通过虚拟音频端点和本机输入法转换为文字，Codex 快捷键与输入法语音快捷键是两套独立配置。
- **先用键盘验证输入法快捷键**：豆包、微信输入法或其他语音工具的快捷键和触发方式可能不同，确认键盘可用后再排查遥控器。
- **上下键不是六个固定槽位**：当前实现循环切换“最近查看的会话”，会话顺序可能随使用变化；左右键仍保留为普通方向键。
- **避免同时连接两只同型遥控器**：发现多个匹配设备时程序会拒绝猜测，不会随机连接其中一只。
- **返回键或音量键缺失时检查权限页**：部分 Windows 环境需要用户主动启用完整 HID 支持并确认一次 UAC；主桥接仍以普通权限运行。
- **保存后要重启桥接**：连接设备、音频端点或底层按键支持发生变化时，点击“保存并重启桥接”，不要同时启动多个桥接实例。
- **进程运行不等于设备已连接**：需要结合设置页状态和 `%LOCALAPPDATA%\RemoteMic\RC003\logs\app.log` 中的真实连接、HID 与语音记录判断。
- **预设会占用音量键**：Codex 预设把音量 ± 用于推理强度；需要调系统音量时，可在映射页改回“系统音量 + / −”或恢复标准默认值。
- **安装包尚未签名**：SmartScreen 提示属于预期情况；只从本仓库 Release 下载，并按 `SHA256SUMS.txt` 校验文件。

## 设置界面设计

当前 Windows 设置窗口已采用极简扁平化界面：统一浅色语义色板、顶部导航和单个选中按键编辑器。视觉与交互约束见 [设计说明](docs/design/minimal-settings.md)；[早期交互稿](docs/design/minimal-settings.html) 仅保留为设计过程记录，其中的设备状态均为演示数据。

详细配对、虚拟声卡配置、按键映射和故障排查见
[`apps/windows/rc003/README.md`](apps/windows/rc003/README.md)。

## 从源码本地运行

在 Windows PowerShell 中执行：

```powershell
Set-Location apps/windows/rc003
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
.\.venv\Scripts\python.exe -m ovb_rc003 --settings
```

运行桥接（单独的桥接进程）：

```powershell
.\.venv\Scripts\python.exe -m ovb_rc003 --bridge
```

运行测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -p 'test_*.py' -v
```

构建未签名候选版：

```powershell
.\build\build-candidate.ps1
```

完整安装、配对、VB-CABLE 配置、已知限制和发布流程见 [`apps/windows/rc003/README.md`](apps/windows/rc003/README.md)。

## 来源与第三方实现细节

- **直接上游**：[`miaomiaozii/windows-remote-mic-app`](https://github.com/miaomiaozii/windows-remote-mic-app)。Remote Vibe Coding 从该项目的 Windows 分支继续开发，并保留其提交历史、GPL 许可证和来源说明。
- **Fork 自**：[`HD838A/remote-mic-app`](https://github.com/HD838A/remote-mic-app)（无线麦 Remote Mic：把小米蓝牙遥控器 2 Pro / RC003 变成 Mac 语音输入设备）。本仓库只保留并继续维护其中的 Windows RC003 部分，macOS/Swift 部分不在此仓库维护。
- **Windows 上游参考实现**：[`nijez/open-voice-bridge`](https://github.com/nijez/open-voice-bridge)（GPL-3.0-only），提供 WinRT BLE、ATVV 语音协议、Raw Input、SendInput 和 Qt/QML 设置页的参考实现。
- **RC003 HID 旁路参考**：[`xxb26553663-star/remote-bridge-hub`](https://github.com/xxb26553663-star/remote-bridge-hub)（GPL-3.0-only），提供用 Frida Gadget 读取 Windows 普通输入链路拿不到的 RC003 返回/音量 HID 报告的实现思路。

Windows 实现的改动说明与第三方边界见
[`apps/windows/rc003/ATTRIBUTION.md`](apps/windows/rc003/ATTRIBUTION.md)、
[`COPYRIGHT.md`](COPYRIGHT.md) 和 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## 许可证

代码按 `GPL-3.0-only` 发布。完整许可证见 [`LICENSE.md`](LICENSE.md)。

## 维护边界

- 主程序源码只在 `apps/windows/rc003`；
- Windows CI 位于 `.github/workflows/windows-rc003-ci.yml`；
- `device-profiles` 只保留 Windows 客户端使用的设备目录；
- `LICENSE.md`、`COPYRIGHT.md`、`THIRD_PARTY_NOTICES.md` 和
  [`apps/windows/rc003/ATTRIBUTION.md`](apps/windows/rc003/ATTRIBUTION.md) 保留 GPL
  与上游来源义务，不代表继续维护原 macOS 应用。
