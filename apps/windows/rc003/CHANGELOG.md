# Changelog — Remote Vibe Coding (Windows)

内部构建版本号固定在 `installer/RemoteMicRC003Setup.iss` 的 `AppVersion`
（当前 `0.1.0-candidate`），仓库级 tag 只作为发布编号，两者对应关系以每条
发布说明为准。正式版 tag 格式：`v<内部版本>-windows`；候选版为
`v<内部版本>-windows-rc003-candidate.<序号>`。

## [Unreleased]

### 新增

- 设置页增加“保存并重启桥接”：先请求现有桥接走正常清理路径断开 BLE、音频与按键状态，确认旧实例停止后再启动新桥接；停止超时或失败时禁止叠加启动。

### 修复

- 语音键长按期间的 F5 自动重复不再进入 Raw Input 配对等待，避免释放后积压事件再次唤醒语音，以及全局键盘和输入法持续卡顿。
- 右 Alt 按住模式先发送完整的程序化右 Alt，并以微信语音窗口是否实际出现作为成功判据；未被微信接受时自动释放 Alt，再通过工具栏兜底。隐藏工具栏保持在微信保存的显示器位置，不再移动到虚拟桌面外，避免 Codex 全屏、多显示器和竖屏环境中无法唤醒。
- 工具栏兜底改为保存原窗口区域、以空绘制区域点击后再恢复，避免语音界面前闪出中间窗口；低级键盘钩子只负责立即吞掉遥控器 F5，耗时的微信唤醒移到钩子外执行，防止 Windows 因回调超时移除钩子后再次泄漏 F5。
- RC003 的物理 F5 被确认并吞掉后，同一次按压期间由蓝牙/HID 链路补发的注入 F5 也会被关联吞掉；关联窗口结束后仍放行其他软件的注入按键。
- 右 Alt 按住模式不再先发送微信可能延迟处理的程序化按键，而是直接使用无绘制工具栏入口；同一次 HOLD 音频会话只允许一次唤醒，避免音频与 F5 双通道连续点击后把刚打开的语音窗口重新关闭。

## [0.1.0] — 2026-07-31

标签：`v0.1.0-windows`（基于 `271ed79`）

正式发布。本版本在真实 RC003 遥控器上完成逐键、语音链路验收（方向/OK/Home/
Menu/TV/Power/返回/音量± 单次触发，麦克风键启动豆包输入法并识别语音），
内容与候选版 `v0.1.0-windows-rc003-candidate.1` 相同。

## [0.1.0-candidate] — 2026-07-31

标签：`v0.1.0-windows-rc003-candidate.1`（基于 `6c33fcc`）

首个 Windows RC003 候选发布。本版本已在真实 RC003 遥控器上完成逐键、
语音链路验收（详见 README“真机验收”部分）。CI 与自动构建仍然不能
替代真机验证。

### 新增

- **Frida HID tap 旁路**：对 Windows 普通输入链路拿不到的返回、音量+、
  音量- 缺失 usages（`0xF1`、`0x80`、`0x81`），复用上游
  `remote-bridge-hub` 的 Frida Gadget WUDFHost tap 读取；扩展为上报
  遥控器全部键盘 usage，作为所有普通按键的输入旁路。Gadget 是可选的
  第三方二进制，需显式获取（`build/fetch-frida-gadget.ps1`）且验证
  固定 SHA-256 后才会启用。
- **豆包语音触发（DoubaoPhysicalizer）**：注入的右 Alt 合成事件此前被
  豆包输入法 `ImeService` 的低层键盘钩子以 `LLKHF_INJECTED` 标志忽略；
  现在附加到 `ImeService.exe` 的低层回调，只对该标记事件清除 injected /
  lower-integrity 标志并清空 `dwExtraInfo`，使豆包看到的按键形状与
  实体右 Alt 一致。默认按住模式 `ralt`、切换模式 `ralt+space`。
- **设置页独立入口**：`RemoteMicRC003Settings.exe` 与桥接 EXE 分离
  （后合并为单个 EXE，见下）。
- **按键采集/回放工具**：`src/rc003_key_test.py`、`rc003_key_probe.py`
  等诊断工具，被动记录真实物理签名，不执行映射动作。

### 修复

- **普通按键双触发**：方向键、OK 等按键按下时一次动作被触发两次。
  根因是低层键盘钩子阻塞了 `WM_INPUT` 派发，导致“先 arm 后吞键”的
  等待式方案永远慢半拍。改为由 Frida GATT tap 的独立 socket 线程在
  `NtDeviceIoControlFile` 报告到达时 arm，低层钩子零等待匹配并吞掉
  原生按键，只注入一次映射动作。方向/OK/Home/Menu/TV/Power/返回/
  音量键全部实测通过。
- **F5 语音键重复替换刷屏**：按住麦克风键期间键盘 auto-repeat 会让
  “替换为右 Alt”逻辑反复触发；为 transform 增加已按下/已发送守卫，
  只在真实按下/释放边沿各发送一次。
- **BLE GATT 特征找不到**：修复后反复出现
  `ATVV characteristic not found`；改用 `BluetoothCacheMode.UNCACHED`
  读取服务与特征，避免 Windows 缓存旧枚举结果。
- **设置保存失败且映射不生效**：配置文件改为临时文件 + fsync +
  `os.replace` 原子写入；Qt 设置保存捕获一切持久化/回读异常并在界面
  显示错误；桥接进程在按键前按 mtime 热加载新的按键映射，磁盘数据
  损坏时保留最后一份有效映射。
- **启动闪黑色命令行窗口**：桥接启动子进程与打包运行时的控制台子进程
  均使用 `CREATE_NO_WINDOW` 隐藏。
- **语音识别无声/不稳定**：语音输出改为按端点能力输出立体声并复制
  声道；解码后增加 20 Hz 一阶高通 DC 阻挡；默认增益提高到 +10 dB；
  16 kHz → 48 kHz 改有状态连续插值（对齐上游）。实机验收：豆包输入法
  能识别遥控器语音。

### 变更

- **单 EXE 行为**：合并为同一个 `RemoteMicRC003.exe`。双击（无参数）或
  `--settings` 打开设置窗口；`--bridge` 显式启动桥接进程。安装器/便携版
  的启动快捷方式统一使用 `--bridge`。
- **设置保存原子化**：`save_config` / `save_key_bindings` 走原子写入，
  不暴露半写的 JSON。
- **返回键默认映射**：保持 `delete_backward`（退格）语义；新增可选的
  “浏览器后退”动作供用户在设置页手动绑定。
- 普通按键仍通过 `SendInput` 注入映射动作；语音快捷键通过物理化的
  右 Alt 事件；两者互不混用。

### 已知限制

- 未签名，首次运行会触发 SmartScreen 提示，属预期行为。
- Frida Gadget 与 VB-CABLE 均为可选第三方组件；未显式获取/安装时，
  缺失 usages 不会被猜测伪造，语音默认没有虚拟麦克风路由。
- 遥控器没有独立物理静音键；“系统静音”只是可选手动绑定。
- 安装器与便携版运行期配置都写入 `%LOCALAPPDATA%\RemoteMic\RC003`，
  卸载不会自动删除。
