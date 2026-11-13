(() => {
  if (window.__antigravityZhCnInstalled) return;
  window.__antigravityZhCnInstalled = true;

  const exact = new Map(Object.entries({
    "New Conversation": "新建对话",
    "Automations": "自动化",
    "Customizations": "自定义",
    "Projects": "项目",
    "Conversations": "对话",
    "Settings": "设置",
    "General": "常规",
    "Application": "应用",
    "Appearance": "外观",
    "Shortcuts": "快捷键",
    "Notifications": "通知",
    "Models": "模型",
    "Browser": "浏览器",
    "Not in Project": "不在项目中",
    "Give Feedback": "提交反馈",
    "Close": "关闭",
    "Knowledge Work": "知识工作",
    "Software Engineering": "软件工程",
    "Global Permissions": "全局权限",
    "Learn more": "了解更多",
    "Permission Preset": "权限预设",
    "Tool Permissions": "工具权限",
    "Network Access Rules": "网络访问规则",
    "Agent Behavior": "代理行为",
    "Plan Review Policy": "计划审查策略",
    "Always Ask": "始终询问",
    "Execution": "执行",
    "Queued Messages": "排队消息",
    "Keyboard shortcuts": "键盘快捷键",
    "Voice mode": "语音模式",
    "Voice": "音色",
    "Change": "更改",
    "Microphone": "麦克风",
    "System default": "系统默认",
    "Volume": "音量",
    "Interface Layout": "界面布局",
    "Configure agent execution, queued message delivery, and permissions.": "配置代理执行、排队消息发送和权限。",
    "Configure global allowed and denied resource permissions.": "配置全局允许和拒绝的资源权限。",
    "Simplified interface for research, writing, and everyday tasks.": "适用于研究、写作和日常任务的简化界面。",
    "Full interface for coding, developer tools, and managing agents.": "适用于编程、开发者工具和管理代理的完整界面。",
    "Controls the actions the agent can take.": "控制代理可以执行的操作。",
    "Modify permissions for file, terminal, and MCP tools.": "修改文件、终端和 MCP 工具的权限。",
    "Configure allowed and denied URLs for reading.": "配置允许和拒绝读取的 URL。",
    "Configure when follow-up messages are sent.": "配置后续消息的发送时机。",
    "Input device for voice mode and dictation.": "语音模式和听写使用的输入设备。",
    "How loud Antigravity's voice is.": "设置 Antigravity 语音音量。",
    "Open": "打开",
    "Queue": "排队",
    "Send Immediately": "立即发送",
    "Whether the agent asks you to review its documents.": "代理是否要求你审查它生成的文档。",
    "Modified in": "设置来源：",
    "Type": "输入",
    "and select": "并选择",
    "to have the agent generate a plan.": "让代理生成计划。",
    "Create New Project": "创建新项目",
    "Display Options": "显示选项",
    "Project options": "项目选项",
    "Project Settings": "项目设置",
    "Copy Project Name": "复制项目名称",
    "Reveal in Finder": "在访达中显示",
    "Delete Project": "删除项目",
    "No conversations yet": "暂无对话",
    "Ask anything, @ to mention, / for actions": "输入内容，@ 提及，/ 使用操作",
    "Start Voice mode": "开始语音模式",
    "Record voice memo": "录制语音备忘",
    "Select model": "选择模型",
    "Agent permissions preset selector": "代理权限预设",
    "Toggle Overview Panel": "切换概览面板",
    "Toggle Sidebar": "切换侧栏",
    "Toggle Side Panel": "切换侧面板",
    "Search Conversations": "搜索对话",
    "Maximize Pane": "最大化面板",
    "Go Back": "后退",
    "Go Forward": "前进",
    "Refresh": "刷新",
    "More actions": "更多操作",
    "More options": "更多选项",
    "Add context": "添加上下文",
    "Send message": "发送消息",
    "Copy": "复制",
    "Copy code": "复制代码",
    "Cancel": "取消",
    "Close Window": "关闭窗口",
    "Close": "关闭",
    "New Window": "新建窗口",
    "All Windows": "全部窗口",
    "Working": "处理中",
    "Worked for": "已处理",
    "Model unavailable, retrying": "模型暂不可用，正在重试",
    "User cancelled agent execution.": "用户已取消代理执行。",
    "Agent execution terminated due to error.": "代理执行因错误终止。",
    "Error": "错误",
    "just now": "刚刚",
    "ago": "前",
    "Conversation Log": "对话记录",
    "You said": "你说",
    "Agent said": "代理说",
    "Agent working": "代理处理中",
    "Load older messages": "加载更早消息",
    "Pin conversation": "固定对话",
    "Archive conversation": "归档对话",
    "Stop execution": "停止执行",
    "Good response": "回答满意",
    "Bad response": "回答不满意",
    "Directory Viewer": "目录查看器",
    "File path breadcrumbs": "文件路径",
    "Announcements and tips": "公告与提示",
    "Select project": "选择项目",
    "Branch": "分支",
    "Showing": "显示",
    "of": "共",
    "items": "项",
  }));

  const attributeNames = ["aria-label", "title", "placeholder", "data-tooltip"];
  const skipTags = new Set(["SCRIPT", "STYLE", "CODE", "PRE", "TEXTAREA"]);

  function shouldSkip(element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;
    if (skipTags.has(element.tagName)) return true;
    return Boolean(element.closest("[data-antigravity-zh-skip], .monaco-editor, .view-lines"));
  }

  function translate(value) {
    if (!value || typeof value !== "string") return value;
    const trimmed = value.trim();
    if (!trimmed) return value;
    if (exact.has(trimmed)) {
      return value.replace(trimmed, exact.get(trimmed));
    }
    let result = value;
    result = result.replace(/Showing (\d+)-(\d+) of (\d+) items?/i, "显示第 $1-$2 项，共 $3 项");
    result = result.replace(/Model unavailable, retrying in ([^\n]+)/i, "模型暂不可用，正在重试（$1）");
    result = result.replace(/Good to see you, ([^!]+)! What's next\?/i, "很高兴见到你，$1！接下来做什么？");
    result = result.replace(/Good to see you, ([^.]+)\. What's next\?/i, "很高兴见到你，$1！接下来做什么？");
    result = result.replace(/Hey ([^,]+), what should we build today\?/i, "嗨，$1，今天我们构建什么？");
    result = result.replace(/Whether the agent asks you to review its documents\. Modified in/i, "代理是否要求你审查它生成的文档。设置来源：");
    result = result.replace(/The voice used in Voice mode\. Powered by Gemini Live\./i, "语音模式使用的音色，由 Gemini Live 提供。");
    result = result.replace(/Type \/ and select plan to have the agent generate a plan\./i, "输入 / 并选择 plan，让代理生成计划。");
    result = result.replace(/Select model, current:\s*(.+)/i, "选择模型，当前：$1");
    result = result.replace(/Agent permissions preset selector, current:\s*(.+)/i, "代理权限预设，当前：$1");
    result = result.replace(/current:\s*(.+)/i, "当前：$1");
    result = result.replace(/Worked for (\d+)m?/i, "已处理 $1 分钟");
    result = result.replace(/(\d+) task running/i, "有 $1 个任务运行中");
    result = result.replace(/(\d+)d ago/i, "$1 天前");
    result = result.replace(/(\d+)h ago/i, "$1 小时前");
    result = result.replace(/(\d+)m ago/i, "$1 分钟前");
    return result;
  }

  function translateTextNode(node) {
    const parent = node.parentElement;
    if (!parent || shouldSkip(parent)) return;
    const next = translate(node.nodeValue || "");
    if (next !== node.nodeValue) node.nodeValue = next;
  }

  function translateElement(element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE || shouldSkip(element)) return;
    for (const name of attributeNames) {
      if (!element.hasAttribute(name)) continue;
      const value = element.getAttribute(name);
      const next = translate(value);
      if (next !== value) element.setAttribute(name, next);
    }
  }

  function apply(root) {
    if (!root) return;
    if (root.nodeType === Node.TEXT_NODE) {
      translateTextNode(root);
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE || shouldSkip(root)) return;
    translateElement(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) nodes.push(node);
    for (const textNode of nodes) translateTextNode(textNode);
    for (const element of root.querySelectorAll("*")) translateElement(element);
  }

  apply(document.body || document.documentElement);
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === "characterData") translateTextNode(mutation.target);
      if (mutation.type === "attributes") translateElement(mutation.target);
      for (const node of mutation.addedNodes) apply(node);
    }
  });
  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    characterData: true,
    attributes: true,
    attributeFilter: attributeNames,
  });
})();
