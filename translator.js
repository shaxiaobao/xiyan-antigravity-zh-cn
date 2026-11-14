(() => {
  if (window.__antigravityZhCnInstalled) return;
  window.__antigravityZhCnInstalled = true;

  const exact = new Map(Object.entries(window.__antigravityZhCnDictionary || {}));

  const attributeNames = ["aria-label", "title", "placeholder", "data-tooltip"];

  function shouldSkip(element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;
    return Boolean(element.closest("script, style, code, pre, textarea, input, [contenteditable]:not([contenteditable='false']), [data-antigravity-zh-skip], .monaco-editor, .view-lines"));
  }

  function isContent(element) {
    // Leave message prose, rendered documents, conversation titles and file names alone.
    // Controls inside message areas (copy/retry/review) can still be translated.
    if (element.closest("button, [role='button'], [role='menuitem']")) return false;
    return Boolean(element.closest(".prose, .markdown, .markdown-body, [data-message-author-role], a[href*='/c/'], a[href^='file:']"));
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
    result = result.replace(/^Welcome back, (.+)\. Where should we pick up\?$/i, "欢迎回来，$1。我们从哪里继续？");
    result = result.replace(/^(Select project|Branch), current:\s*(.+)$/i, (_, label, current) => `${exact.get(label) || label}，当前：${current}`);
    result = result.replace(/^(Load older messages), showing (\d+) of (\d+)$/i, "加载更早消息，已显示 $2 条，共 $3 条");
    result = result.replace(/^(Add shortcut for) (.+)$/, (_, label, action) => `添加快捷键：${exact.get(action) || action}`);
    result = result.replace(/^(Remove shortcut|Shortcut) (.+) for (.+)$/, (_, label, keys, action) => `${label === 'Shortcut' ? '快捷键' : '移除快捷键'} ${keys}：${exact.get(action) || action}`);
    result = result.replace(/^Show (\d+) breakdown$/, "显示 $1 项明细");
    result = result.replace(/^(Subagents|Background Tasks|Artifacts|Skills|Rules|Plugins) (\d+)$/, (_, label, count) => `${exact.get(label)} ${count}`);
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
    result = result.replace(/^Worked for (\d+)h(?: (\d+)m)?$/, (_, h, m) => `已处理 ${h} 小时${m ? ` ${m} 分钟` : ''}`);
    result = result.replace(/^Worked for (\d+)m(?: (\d+)s)?$/, (_, m, s) => `已处理 ${m} 分钟${s ? ` ${s} 秒` : ''}`);
    result = result.replace(/^Worked for (\d+)s$/, "已处理 $1 秒");
    result = result.replace(/(\d+) task running/i, "有 $1 个任务运行中");
    result = result.replace(/(\d+)d ago/i, "$1 天前");
    result = result.replace(/(\d+)h ago/i, "$1 小时前");
    result = result.replace(/(\d+)m ago/i, "$1 分钟前");
    return result;
  }

  function translateTextNode(node) {
    const parent = node.parentElement;
    if (!parent || shouldSkip(parent) || isContent(parent)) return;
    const next = translate(node.nodeValue || "");
    if (next !== node.nodeValue) node.nodeValue = next;
  }

  function translateElement(element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return;
    // Translate input labels and placeholders, never input values or editable text.
    if (element.closest(".monaco-editor, .view-lines, [data-antigravity-zh-skip]")) return;
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
    if (root.nodeType !== Node.ELEMENT_NODE) return;
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
