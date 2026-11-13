# 希言-Antigravity-汉化包

Antigravity 的简体中文外置汉化包。当前针对 Antigravity 2.31.x，采用启动后注入翻译脚本的方式工作，不修改项目源代码，也不依赖网络。

下载发布包：<https://github.com/shaxiaobao/xiyan-antigravity-zh-cn/releases/latest>

## 安装

1. 下载或克隆本仓库。
2. 完全退出 Antigravity。
3. 在本目录运行：

```bash
python3 patch_asar.py status
python3 patch_asar.py apply
```

4. 重新打开 Antigravity。

补丁会翻译侧栏、设置页、项目菜单、对话操作、权限设置、执行设置、语音设置、输入提示和常见状态信息。代码块、命令、URL、编辑器内容和用户业务数据会保留原文。

## 恢复官方版本

```bash
python3 patch_asar.py restore
```

安装时工具会在本目录生成原始 `app.asar` 备份。恢复前会校验当前文件是否仍由本工具生成，避免覆盖 Antigravity 更新后的新版本。

## 应用更新后

应用升级后先运行 `status`。如果版本指纹发生变化，重新执行 `apply` 为新版本生成补丁。应用更新可能覆盖补丁，这是正常现象。

## 注意事项

- 这是外置补丁，不是 Antigravity 官方插件。
- 补丁只修改 Antigravity 的 `app.asar`，不会修改你的项目文件。
- 如果 Antigravity 安装位置不是 `/Applications/Antigravity.app`，请先修改 `patch_asar.py` 中的 `APP_ASAR`。
