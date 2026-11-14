# 希言-Antigravity-汉化包

独立维护的 Antigravity 简体中文语言包，包含外置词库、界面翻译引擎和 macOS / Windows 中文启动入口。macOS 已在 Antigravity **2.32.1** 实机验证；Windows 为实验性适配，安装器流程可通过 Windows CI 验证，真实应用界面尚未实机验收。

[下载最新版](https://github.com/shaxiaobao/xiyan-antigravity-zh-cn/releases/latest)

## 推荐：下载安装器，无需安装 Python

1. 在 Release 下载 `xiyan-installer` 开头、与系统对应的 ZIP：Windows x64、Mac Apple 芯片 arm64 或 Mac Intel x64。
2. 解压后打开 `XiyanAntigravityChinese.exe`（Windows）或 `XiyanAntigravityChinese.app`（Mac）。
3. 保存工作，完全退出 Antigravity。在安装器中确认位置，点击 **安装／修复汉化**。
4. 完成后关闭安装器，从原来的 Antigravity 图标打开，即为中文。也可以点击 **打开 Antigravity**。

以后正常使用原图标，不必经过中文启动器。应用更新可能覆盖汉化，重新打开安装器点击“安装／修复汉化”即可。恢复英文也在同一个窗口操作。安装器不会强制结束任务、常驻后台或自动提权。

Mac 如出现写入权限错误，请检查“系统设置 → 隐私与安全性 → App 管理”中的安装器权限。Windows 安装在 Program Files 等受保护目录时，需要应用所有者处理写入权限。安装器目前未经过 Apple 公证或 Windows 商业代码签名，系统可能显示来源提示。

安装器内置运行环境与 356 条翻译。Mac arm64 为本机打包；Windows 与 Mac Intel 包由对应平台 CI 构建并运行内置运行环境测试。Windows 实际 Antigravity 界面仍待实机验收，不同架构的应用资源不保证兼容。

## 旧版升级与备份

已经使用 v0.1–v0.3 的用户：先在新安装器中选择应用位置，再点 **导入旧版备份…**，选择旧语言包目录中的 `patch-state.json` 文件（旁边的 `backups` 目录需保留）。导入会校验当前补丁及原始备份，不会删除旧文件。之后即可安装或恢复。没有有效备份时，不会强行覆盖未知补丁。

新版安装器的备份与状态独立保存在以下目录，按应用路径分开管理：

- Mac：`~/Library/Application Support/XiyanAntigravityChinese/`
- Windows：`%LOCALAPPDATA%\XiyanAntigravityChinese\`

因此移动安装器不会丢失备份。恢复英文后可以删除安装器；保留数据目录可供后续排查。安装中断时若出现锁文件或 pending 文件提示，请保留它们并反馈，不要直接删除状态后重装。

## 开发者脚本入口

源码仍支持 Python 3.9+ 的命令入口；普通用户请下载上方安装器，不用下载 GitHub 的 Source code。

```bash
python3 patch_asar.py status
python3 patch_asar.py apply
python3 patch_asar.py restore
python3 patch_asar.py --app "/Applications/Antigravity.app" apply
```

Windows 可使用 `py -3`，`--app` 接受安装目录、Antigravity.exe 或 app.asar。也可用 `ANTIGRAVITY_PATH` 环境变量指定路径。旧 `.command/.cmd` 中文启动入口仍保留供旧版用户使用。

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

## 构建与验证

```bash
python3 -m unittest -v test_patch_asar.py test_installer_service.py
python3 -m pip install pyinstaller==6.16.0
python3 build_installer.py
python3 package_installer.py
```

在目标操作系统上打包；Windows 构建 EXE，Mac 构建 APP。发布流程包含资源完整性、运行中保护、并发安装保护、状态写入失败回滚、旧备份导入和打包后 Tk/词库加载测试。离线测试使用模拟 ASAR，不代表真实应用界面验收。

## 许可证：允许非商业使用，禁止商用

Copyright © 2026 shaxiaobao（希言）。本项目采用 [希言非商业源码许可协议 1.0](LICENSE)。

- 允许个人学习、非商业教学研究、非商业修改和免费分享。
- 使用或分享时必须保留版权声明、项目地址和完整许可证；修改版必须标明修改，继续遵守非商业限制。
- 未经另行书面许可，不得收费分发、提供收费服务、用于商业产品、商业经营或有偿工作。商用须向版权人申请独立授权。

这是源码可用项目，不属于符合 OSI 定义的开源软件。许可证仅覆盖本项目有权许可的内容，不授予 Antigravity 或其他第三方软件的权利。完整条款以 LICENSE 为准。
