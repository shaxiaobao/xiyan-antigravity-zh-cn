# 希言-Antigravity-汉化包

独立维护的 Antigravity 简体中文语言包，包含外置词库、界面翻译引擎和 macOS / Windows 中文启动入口。macOS 已在 Antigravity **2.32.1** 实机验证；Windows 为实验性适配，安装器流程可通过 Windows CI 验证，真实应用界面尚未实机验收。

[下载最新版](https://github.com/shaxiaobao/xiyan-antigravity-zh-cn/releases/latest)

## macOS 使用

1. 下载 Release ZIP，解压后保留整个文件夹。
2. 安装 Python 3.9 或更新版本（已有 Python 3 的电脑无需重复安装）。
3. 首次使用前完全退出 Antigravity，然后双击 **希言 Antigravity 中文启动器.app**。也可双击 **启动 Antigravity 中文版.command**。
4. 以后通过这个中文入口打开，可将 `.app` 拖到 Dock 的应用区域方便使用。不要单独移动 `.app`；它需要与语言包文件保存在同一文件夹。

macOS 可能要求为中文启动器开启“系统设置 → 隐私与安全性 → App 管理”权限，因为兼容加载器需要写入 Antigravity 应用资源。该权限由你自行决定是否授予，工具不会自动开启。未授权时会停止安装并显示错误，不会关闭系统保护。首次授权后需重新运行中文入口；若出现 `Operation not permitted`，请检查此权限。

## Windows 使用（实验性）

1. 下载文件名含 `windows` 的 ZIP，解压到自己可写的固定目录，保留全部文件。
2. 安装 Python 3.9 或更新版本，确保 `py -3` 或 `python` 命令可用。
3. 完全退出 Antigravity，双击 **启动 Antigravity 中文版.cmd**。可以为此文件创建桌面快捷方式。
4. 启动器自动查找 `%LOCALAPPDATA%\Programs\Antigravity`、`%LOCALAPPDATA%\Antigravity`、`%ProgramFiles%\Antigravity` 和 `%ProgramFiles(x86)%\Antigravity`。

自定义安装目录可通过 `ANTIGRAVITY_PATH` 环境变量指定，或在终端使用以下命令（路径替换成实际位置）：

```bat
py -3 patch_asar.py --app "D:\Apps\Antigravity" launch
py -3 patch_asar.py --app "D:\Apps\Antigravity" status
py -3 patch_asar.py --app "D:\Apps\Antigravity" restore
```

`--app` 也接受 `Antigravity.exe` 或 `resources\app.asar` 的完整路径。发现多个安装位置时会要求明确选择。安装在 Program Files 等受保护目录时，需要应用所有者提供写入权限；脚本不会自动提权。进程检测失败或应用正在运行时不会安装补丁。窗口关闭不一定代表程序退出，请检查托盘和任务管理器。

Windows 版本必须包含兼容的 `resources/app.asar` 与 `/dist/utils.js` 加载结构。不同产品架构或版本不保证兼容；不兼容时会停止，不会尝试绕过应用完整性保护。Windows 支持状态与 macOS 实测结论分别记录。

## 更新后保持中文

启动器在应用未运行时检查补丁：应用升级覆盖补丁后，会为当前版本建立独立备份、检查注入位置，再重新安装汉化。词库更新也会自动重新生成补丁。若应用已经运行，启动器只打开现有窗口，不强制结束代理或后台任务；需完全退出后再用中文入口打开。

**直接点击原版 Antigravity 图标，会绕过上述检查。** 原版图标在更新覆盖补丁之后仍可能打开英文界面。未来版本如果改变了界面结构或加载机制，需要继续适配；此项目不承诺任意版本永久兼容。

## 汉化范围

- 侧栏、欢迎语、项目和对话菜单、输入提示、模型选择和常见执行状态。
- 常规、应用、外观、快捷键、通知、模型与用量、浏览器设置。
- 权限、文件读写规则、项目设置、自定义市场和自动化页面的常见标签。
- 文件、终端、审查、子代理、后台任务等面板的常见名称。
- 带当前模型、数量、按键组合等内容的动态标签。

当前词库共 356 条固定映射，另有动态匹配规则。新增词库不代表所有隐藏页面均已验证。macOS 原生菜单、系统弹窗、第三方插件或网页、模型输出和新增页面仍可能显示英文。代码、输入值、常见 Markdown 正文区域和对话标题会跳过翻译；不会修改项目文件或聊天数据库。

## 为什么不是普通插件

目前 Antigravity 常规插件没有替换整个主界面的公开接口。本项目是**第三方中文语言包加兼容加载器**，并非官方插件或原生语言选项。词库保存在独立的 `translations.json`，加载器仍需要修改应用资源 `app.asar`；应用更新后使用中文启动器重新应用。

语言包不请求联网、不启动调试端口、不关闭应用更新或系统安全保护，也不安装后台常驻服务。

## 从旧版升级

用新版源文件和启动器覆盖原语言包目录，保留原来的 `patch-state.json` 和 `backups/`，然后完全退出 Antigravity 并使用中文入口重新打开。也可先在旧目录运行 `restore`，再安装新目录中的语言包。不要删除状态文件后强行安装：新目录无法识别另一目录安装的补丁时会拒绝覆盖。

启动失败时可查看同目录 `launcher.log`，或双击 `.command` 入口查看错误。日志仅记录安装状态和错误，不记录对话内容。

## 命令行

在本目录运行：

```bash
python3 patch_asar.py status   # 查看当前版本和汉化状态
python3 patch_asar.py apply    # 安装或更新兼容补丁
python3 patch_asar.py launch   # 检查补丁并启动，保留运行中的任务
python3 patch_asar.py restore  # 恢复当前版本原始资源
```

macOS 默认查找 `/Applications/Antigravity.app` 和用户的 `~/Applications/Antigravity.app`；自定义位置可使用 `--app` 参数。若目录无写权限，应由应用所有者处理权限；工具不会自动提权。

备份按原始文件指纹保存在 `backups/`，旧备份保留。恢复会校验当前补丁与备份；应用升级后不会用旧版备份覆盖新版。请保留本目录和备份，不要通过删除状态文件来强行覆盖未知修改。

## 开发与打包

```bash
python3 -m unittest -v test_patch_asar.py
node --check translator.js
python3 build_mac_launcher.py   # macOS，自带 osacompile
python3 build_release.py --platform macos
python3 build_release.py --platform windows
```

回归测试使用临时模拟应用，不写入已安装的 Antigravity，覆盖版本升级、词库更新、重复安装、恢复校验、未知修改保护和启动顺序。修改 `translations.json` 后，完全退出 Antigravity，再从中文入口打开即可加载。

## 许可证：允许非商业使用，禁止商用

Copyright © 2026 shaxiaobao（希言）。本项目采用 [希言非商业源码许可协议 1.0](LICENSE)。

- 允许个人学习、非商业教学研究、非商业修改和免费分享。
- 使用或分享时必须保留版权声明、项目地址和完整许可证；修改版必须标明修改，继续遵守非商业限制。
- 未经另行书面许可，不得收费分发、提供收费服务、用于商业产品、商业经营或有偿工作。商用须向版权人申请独立授权。

这是源码可用项目，不属于符合 OSI 定义的开源软件。许可证仅覆盖本项目有权许可的内容，不授予 Antigravity 或其他第三方软件的权利。完整条款以 LICENSE 为准。
