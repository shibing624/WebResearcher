// ============ DOM 元素引用 ============
const $ = (id) => document.getElementById(id);

// 侧边栏
const historySidebar = $("historySidebar");
const showSidebarBtn = $("showSidebarBtn");
const mainContent = $("mainContent");
const historyList = $("historyList");
const historyEmpty = $("historyEmpty");
const newResearchBtn = $("newResearchBtn");

// 主面板
const mainPanel = $("mainPanel");
const messagesContainer = $("messagesContainer");
const messagesList = $("messagesList");
const welcomeSection = $("welcomeSection");
const researchForm = $("researchForm");
const questionInput = $("questionInput");
const startButton = $("startButton");

// 过程侧边栏
const processSidebar = $("processSidebar");
const toggleProcessBtn = $("toggleProcessBtn");
const processIcon = $("processIcon");
const processEmpty = $("processEmpty");
const processContent = $("processContent");

// 设置对话框
const settingsModal = $("settingsModal");
const settingsBtn = $("settingsBtn");
const closeSettings = $("closeSettings");
const cancelSettings = $("cancelSettings");
const saveSettings = $("saveSettings");
const agentInput = $("agentInput");
const ttsNumAgentsInput = $("ttsNumAgentsInput");
const maxTurnsInput = $("maxTurnsInput");
const instructionInput = $("instructionInput");
const toolsInput = $("toolsInput");

// 移动端元素
const mobileOverlay = $("mobileOverlay");
const mobileMenuBtn = $("mobileMenuBtn");
const mobileProcessBtn = $("mobileProcessBtn");

// ============ 全局状态 ============
const state = {
  eventSource: null,
  currentSessionId: null,
  currentQuestion: null,
  sidebarCollapsed: false,
  processCollapsed: false,
  isResearching: false,
  isMobile: false, // 是否为移动端
  settings: {
    agent: "web_researcher",
    ttsNumAgents: 3,
    maxTurns: 5,
    instruction: "",
    tools: [],
  },
  // 当前会话的对话历史
  conversationHistory: [],
  // 当前正在进行的研究过程（仅用于实时流式显示）
  currentProcess: {
    rounds: [],     // 简化为数组
    toolCalls: [],  // 简化为数组
  },
  // Web Weaver 当前阶段（planner/writer），用于将 step 映射为 round
  webWeaverPhase: "planner",
};

// ============ 工具函数 ============
const escapeHtml = (text = "") =>
  String(text).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char] || char));

const formatMarkdown = (text = "") => {
  if (!text) return "";
  let html = escapeHtml(text);
  
  // 标题
  html = html.replace(/^### (.*?)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.*?)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.*?)$/gm, "<h1>$1</h1>");
  
  // 粗体
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // 代码块
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
  });
  
  // 行内代码
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  
  // 列表
  html = html.replace(/^\* (.*?)$/gm, "<li>$1</li>");
  html = html.replace(/^- (.*?)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*?<\/li>\n?)+/g, "<ul>$&</ul>");
  
  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-600 hover:underline">$1</a>');
  
  // 段落
  html = html.split('\n\n').map(para => {
    if (!para.trim() || para.startsWith('<') || para.includes('</')) return para;
    return `<p>${para}</p>`;
  }).join('\n');
  
  // 换行
  html = html.replace(/\n/g, "<br/>");
  
  return html;
};

const formatDate = (value) => {
  if (!value) return "";
  try {
    return new Intl.DateTimeFormat("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date(value));
  } catch (error) {
    return value;
  }
};

const parseTools = (value = "") =>
  value
    .split(",")
    .map((token) => token.trim())
    .filter((token) => token.length);

// 自动调整文本框高度（避免单行时出现滚动条）
const autoResizeTextarea = (textarea) => {
  textarea.style.height = 'auto';
  const scrollHeight = textarea.scrollHeight;
  const lineHeight = 24; // 与 CSS 中的 line-height 一致
  
  // 计算实际需要的高度
  const newHeight = Math.min(scrollHeight, 200);
  
  // 只有当内容高度大于单行高度时才设置 height
  if (scrollHeight > lineHeight) {
    textarea.style.height = newHeight + 'px';
  } else {
    textarea.style.height = lineHeight + 'px';
  }
  
  // 控制 overflow-y
  textarea.style.overflowY = scrollHeight > 200 ? 'auto' : 'hidden';
};

// 检测是否为移动端
const checkMobile = () => {
  state.isMobile = window.innerWidth <= 768;
  return state.isMobile;
};

// ============ UI 控制 ============
const toggleSidebar = () => {
  state.sidebarCollapsed = !state.sidebarCollapsed;
  
  if (checkMobile()) {
    // 移动端：使用抽屉式
    if (state.sidebarCollapsed) {
      historySidebar.classList.remove("mobile-open");
      mobileOverlay.classList.remove("active");
    } else {
      historySidebar.classList.add("mobile-open");
      mobileOverlay.classList.add("active");
      // 关闭研究过程面板
      if (processSidebar.classList.contains("mobile-open")) {
        processSidebar.classList.remove("mobile-open");
      }
    }
  } else {
    // 桌面端：原有逻辑
    if (state.sidebarCollapsed) {
      historySidebar.style.transform = "translateX(-100%)";
      mainContent.style.marginLeft = "0";
      showSidebarBtn.classList.remove("hidden");
      showSidebarBtn.classList.add("flex");
      // 箭头向右（展开）
      showSidebarBtn.querySelector("svg path").setAttribute("d", "M9 5l7 7-7 7");
      showSidebarBtn.title = "显示历史记录";
    } else {
      historySidebar.style.transform = "translateX(0)";
      mainContent.style.marginLeft = "260px";
      showSidebarBtn.classList.add("hidden");
      showSidebarBtn.classList.remove("flex");
      // 箭头向左（收起）
      showSidebarBtn.querySelector("svg path").setAttribute("d", "M15 19l-7-7 7-7");
      showSidebarBtn.title = "隐藏历史记录";
    }
  }
};

const toggleProcess = () => {
  state.processCollapsed = !state.processCollapsed;
  
  if (checkMobile()) {
    // 移动端：使用抽屉式
    if (state.processCollapsed) {
      processSidebar.classList.remove("mobile-open");
      mobileOverlay.classList.remove("active");
    } else {
      processSidebar.classList.add("mobile-open");
      mobileOverlay.classList.add("active");
      // 关闭历史记录面板
      if (historySidebar.classList.contains("mobile-open")) {
        historySidebar.classList.remove("mobile-open");
      }
    }
  } else {
    // 桌面端：原有逻辑
    if (state.processCollapsed) {
      processSidebar.style.width = "0";
      processSidebar.style.transform = "translateX(100%)";
      mainPanel.style.marginRight = "0";
      processIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>';
    } else {
      processSidebar.style.width = "480px";
      processSidebar.style.transform = "translateX(0)";
      mainPanel.style.marginRight = "0";
      processIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>';
    }
  }
};

// 关闭所有移动端面板
const closeMobilePanels = () => {
  if (checkMobile()) {
    historySidebar.classList.remove("mobile-open");
    processSidebar.classList.remove("mobile-open");
    mobileOverlay.classList.remove("active");
    state.sidebarCollapsed = true;
    state.processCollapsed = true;
  }
};

const updateTtsNumAgentsVisibility = () => {
  const row = document.getElementById("ttsNumAgentsRow");
  if (row) row.style.display = agentInput?.value === "tts" ? "block" : "none";
};

const showSettings = () => {
  agentInput.value = state.settings.agent || "web_researcher";
  ttsNumAgentsInput.value = state.settings.ttsNumAgents ?? 3;
  maxTurnsInput.value = state.settings.maxTurns ?? 5;
  instructionInput.value = state.settings.instruction;
  toolsInput.value = state.settings.tools.join(", ");
  updateTtsNumAgentsVisibility();
  settingsModal.classList.remove("hidden");
};

agentInput.addEventListener("change", updateTtsNumAgentsVisibility);

const hideSettings = () => {
  settingsModal.classList.add("hidden");
};

// ============ 消息渲染 ============
const addUserMessage = (question) => {
  if (welcomeSection) {
    welcomeSection.remove();
  }
  
  const messageDiv = document.createElement("div");
  messageDiv.className = "message-bubble fade-in";
  messageDiv.innerHTML = `
    <div class="flex justify-end">
      <div class="user-message max-w-xl">
        ${escapeHtml(question)}
      </div>
    </div>
  `;
  
  messagesList.appendChild(messageDiv);
  scrollToBottom();
};

const addAssistantMessage = (content = "", isLoading = true, turnIndex = null) => {
  const messageDiv = document.createElement("div");
  messageDiv.className = "message-bubble assistant-message fade-in";
  messageDiv.dataset.role = "assistant";
  if (turnIndex !== null) {
    messageDiv.dataset.turnIndex = turnIndex;
  }
  
  if (isLoading) {
    messageDiv.innerHTML = `
      <div class="flex gap-3">
        <div class="flex-1 min-w-0">
          <div class="markdown-body">
            <div class="flex items-center gap-2 text-gray-500">
              <svg class="animate-spin w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <span>正在研究...</span>
            </div>
          </div>
        </div>
      </div>
    `;
  } else {
    messageDiv.innerHTML = `
      <div class="flex gap-3 cursor-pointer hover:bg-gray-50 -mx-2 px-2 py-1 rounded-lg transition message-clickable" title="点击查看研究过程">
        <div class="flex-1 min-w-0">
          <div class="markdown-body">
            ${formatMarkdown(content)}
          </div>
        </div>
      </div>
    `;
  }
  
  messagesList.appendChild(messageDiv);
  
  // 绑定点击事件显示对应轮次的研究过程
  if (!isLoading && turnIndex !== null) {
    const clickable = messageDiv.querySelector(".message-clickable");
    if (clickable) {
      clickable.addEventListener("click", () => {
        loadAndShowProcess(turnIndex);
      });
    }
  }
  
  scrollToBottom();
  return messageDiv;
};

const updateAssistantMessage = (messageDiv, content, turnIndex = null) => {
  const existingWrapper = messageDiv.querySelector(".flex.gap-3");
  if (existingWrapper) {
    // 添加点击交互
    existingWrapper.className = "flex gap-3 cursor-pointer hover:bg-gray-50 -mx-2 px-2 py-1 rounded-lg transition message-clickable";
    existingWrapper.setAttribute("title", "点击查看研究过程");
    
    // 移除旧的 onclick
    existingWrapper.removeAttribute("onclick");
    
    // 绑定新的点击事件
    if (turnIndex !== null) {
      messageDiv.dataset.turnIndex = turnIndex;
      existingWrapper.addEventListener("click", () => {
        loadAndShowProcess(turnIndex);
      });
    }
  }
  
  const contentArea = messageDiv.querySelector(".markdown-body");
  if (contentArea) {
    contentArea.innerHTML = formatMarkdown(content);
  }
  scrollToBottom();
};

const scrollToBottom = () => {
  setTimeout(() => {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }, 100);
};

// ============ 加载并显示指定轮次的研究过程 ============
const loadAndShowProcess = async (turnIndex) => {
  // 如果研究过程面板是折叠的，先展开
  if (state.processCollapsed) {
    toggleProcess();
  }
  
  // 显示加载状态
  processEmpty.classList.add("hidden");
  processContent.classList.remove("hidden");
  processContent.innerHTML = '<div class="flex items-center justify-center p-4"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>';
  
  try {
    // 从后端获取该轮次的研究过程
    const response = await fetch(`/api/session/${state.currentSessionId}/turn/${turnIndex}/process`);
    if (!response.ok) {
      throw new Error("获取研究过程失败");
    }
    
    const data = await response.json();
    renderProcessData(data.process);
  } catch (error) {
    console.error("加载研究过程失败", error);
    processContent.innerHTML = `<div class="p-4 text-red-600">加载失败: ${error.message}</div>`;
  }
};

const renderProcessData = (processData) => {
  const items = [];
  
  if (!processData || (!processData.rounds?.length && !processData.tools?.length)) {
    processContent.innerHTML = '<div class="text-center text-gray-500 p-4">暂无研究过程</div>';
    return;
  }
  
  const rounds = processData.rounds || [];
  const tools = processData.tools || [];
  
  // 按轮次组织数据，按照 plan -> report -> tool_call 的顺序
  rounds.forEach((round) => {
    const roundNum = round.round;
    
    // 1. 计划卡片（第一步）
    if (round.plan) {
      items.push(createProcessCard(
        "计划",
        round.plan,
        "purple",
        roundNum,
        round.timestamp
      ));
    }
    
    // 2. 中间报告（第二步）
    if (round.report) {
      items.push(createProcessCard(
        "中间报告",
        round.report,
        "green",
        roundNum,
        round.timestamp
      ));
    }
    
    // 3. 该轮次的工具调用（第三步）
    const roundTools = tools.filter(t => t.round === roundNum);
    roundTools.forEach((tool) => {
      items.push(createProcessCard(
        tool.is_error ? "工具错误" : "工具调用",
        `${tool.tool}\n\n${tool.observation}`,
        tool.is_error ? "red" : "blue",
        roundNum,
        tool.timestamp
      ));
    });
  });
  
  processContent.innerHTML = items.join("");
  
  // 绑定展开事件
  bindProcessCardEvents();
  
  processContent.scrollTop = 0;
};

const bindProcessCardEvents = () => {
  processContent.querySelectorAll(".expand-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const card = e.target.closest(".process-card");
      const preview = card.querySelector(".collapsed-preview");
      const fullContent = card.querySelector(".full-content");
      
      if (preview.classList.contains("hidden")) {
        preview.classList.remove("hidden");
        fullContent.classList.add("hidden");
        card.classList.remove("expanded");
        e.target.textContent = "展开";
      } else {
        preview.classList.add("hidden");
        fullContent.classList.remove("hidden");
        card.classList.add("expanded");
        e.target.textContent = "收起";
      }
    });
  });
};

// ============ 实时流式显示研究过程（仅用于当前正在进行的研究）============
const renderProcess = () => {
  processEmpty.classList.add("hidden");
  processContent.classList.remove("hidden");
  
  const items = [];
  const rounds = state.currentProcess.rounds.sort((a, b) => a.round - b.round);
  
  // 按照 plan -> report -> tool_call 的顺序渲染
  rounds.forEach((round) => {
    // 1. 计划卡片（第一步）
    if (round.plan) {
      items.push(createProcessCard(
        "计划",
        round.plan,
        "purple",
        round.round,
        round.timestamp
      ));
    }
    
    // 2. 中间报告（第二步）
    if (round.report) {
      items.push(createProcessCard(
        "中间报告",
        round.report,
        "green",
        round.round,
        round.timestamp
      ));
    }
    
    // 3. 工具调用（第三步）
    const roundTools = state.currentProcess.toolCalls.filter(t => t.round === round.round);
    roundTools.forEach((tool) => {
      items.push(createProcessCard(
        tool.isError ? "工具错误" : "工具调用",
        `${tool.tool}\n\n${tool.observation}`,
        tool.isError ? "red" : "blue",
        round.round,
        tool.timestamp
      ));
    });
  });
  
  processContent.innerHTML = items.join("");
  bindProcessCardEvents();
  processContent.scrollTop = processContent.scrollHeight;
};

const createProcessCard = (title, content, color, round, timestamp) => {
  const colorMap = {
    purple: { icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2", bg: "bg-purple-50", text: "text-purple-700" },
    blue: { icon: "M13 10V3L4 14h7v7l9-11h-7z", bg: "bg-blue-50", text: "text-blue-700" },
    green: { icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", bg: "bg-green-50", text: "text-green-700" },
    red: { icon: "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z", bg: "bg-red-50", text: "text-red-700" },
  };
  
  const theme = colorMap[color] || colorMap.blue;
  const needsExpand = content.length > 200;
  const previewContent = needsExpand ? content.substring(0, 200) : content;
  
  return `
    <div class="process-card p-3 fade-in">
      <div class="flex items-start gap-2">
        <div class="flex-shrink-0 w-6 h-6 ${theme.bg} rounded flex items-center justify-center">
          <svg class="w-3.5 h-3.5 ${theme.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${theme.icon}"/>
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1">
            <span class="font-medium ${theme.text} text-[0.95rem]">${title}</span>
            <span class="text-gray-400 text-[0.7rem]">#${round}</span>
          </div>
          <div class="text-gray-700 leading-relaxed">
            ${needsExpand ? `
              <div class="collapsed-preview">
                ${escapeHtml(previewContent)}...
              </div>
              <div class="full-content hidden">
                ${escapeHtml(content)}
              </div>
              <div class="expand-btn">展开</div>
            ` : `
              <div>${escapeHtml(content)}</div>
            `}
          </div>
        </div>
      </div>
    </div>
  `;
};

// 将 Web Weaver 的 step 映射为 round（planner: 1-N, writer: 101-N）
const stepToRound = (step, phase) => {
  const p = phase || state.webWeaverPhase;
  return (p === "writer" ? 100 : 0) + (step || 1);
};

// ============ 数据处理 ============
const processEvent = (event) => {
  if (!event || !event.type) return;
  
  const turnIndex = event.turn_index !== undefined ? event.turn_index : state.conversationHistory.length;

  switch (event.type) {
    case "round": {
      const roundNum = event.round || 1;
      
      // 查找是否已存在该轮次
      let round = state.currentProcess.rounds.find(r => r.round === roundNum);
      if (!round) {
        round = {
          round: roundNum,
          plan: "",
          report: "",
          timestamp: event.timestamp || new Date().toISOString(),
        };
        state.currentProcess.rounds.push(round);
      }
      
      // 更新计划和报告
      if (event.plan) round.plan = event.plan;
      if (event.report) round.report = event.report;
      if (event.timestamp) round.timestamp = event.timestamp;
      
      renderProcess();
      break;
    }

    case "step": {
      // Web Weaver: step 对应一轮，映射为 round；若有 plan 则写入
      const roundNum = stepToRound(event.step, event.phase);
      let round = state.currentProcess.rounds.find(r => r.round === roundNum);
      if (!round) {
        round = {
          round: roundNum,
          plan: "",
          report: "",
          timestamp: event.timestamp || new Date().toISOString(),
        };
        state.currentProcess.rounds.push(round);
      }
      if (event.plan) round.plan = event.plan;
      if (event.timestamp) round.timestamp = event.timestamp;
      // tool_call 类型的 step 由 tool 事件单独处理
      renderProcess();
      break;
    }

    case "outline_updated": {
      const roundNum = stepToRound(event.step, event.phase);
      let round = state.currentProcess.rounds.find(r => r.round === roundNum);
      if (!round) {
        round = {
          round: roundNum,
          plan: "",
          report: "",
          timestamp: event.timestamp || new Date().toISOString(),
        };
        state.currentProcess.rounds.push(round);
      }
      if (event.outline) round.report = event.outline;
      if (event.timestamp) round.timestamp = event.timestamp;
      renderProcess();
      break;
    }

    case "section_written": {
      const roundNum = stepToRound(event.step, event.phase);
      let round = state.currentProcess.rounds.find(r => r.round === roundNum);
      if (!round) {
        round = {
          round: roundNum,
          plan: "",
          report: "",
          timestamp: event.timestamp || new Date().toISOString(),
        };
        state.currentProcess.rounds.push(round);
      }
      if (event.content) {
        round.report = (round.report ? round.report + "\n\n" : "") + event.content;
      }
      if (event.timestamp) round.timestamp = event.timestamp;
      renderProcess();
      break;
    }

    case "thinking": {
      // React Agent: 思考/推理内容，创建 round 并作为 plan 展示
      const roundNum = event.round || 1;
      let round = state.currentProcess.rounds.find(r => r.round === roundNum);
      if (!round) {
        round = {
          round: roundNum,
          plan: "",
          report: "",
          timestamp: event.timestamp || new Date().toISOString(),
        };
        state.currentProcess.rounds.push(round);
      }
      if (event.content) round.plan = (round.plan ? round.plan + "\n\n" : "") + event.content;
      if (event.timestamp) round.timestamp = event.timestamp;
      renderProcess();
      break;
    }

    case "tool":
    case "tool_error": {
      // Web Weaver 用 event.step，Web Researcher/React 用 event.round
      const roundNum = event.round !== undefined ? event.round : stepToRound(event.step, event.phase);
      // React 不发送 round 事件，需确保 round 存在才能被 renderProcess 展示
      let r = state.currentProcess.rounds.find(x => x.round === roundNum);
      if (!r) {
        r = {
          round: roundNum,
          plan: "",
          report: "",
          timestamp: event.timestamp || new Date().toISOString(),
        };
        state.currentProcess.rounds.push(r);
      }
      state.currentProcess.toolCalls.push({
        round: roundNum,
        tool: event.tool_call || event.action || event.tool_name || "tool",
        observation: event.observation || "",
        timestamp: event.timestamp || new Date().toISOString(),
        isError: event.type === "tool_error",
      });
      
      renderProcess();
      break;
    }

    case "tts_result": {
      // TTS Agent: 并行研究结果，转为 rounds 展示
      const runs = event.parallel_runs || [];
      runs.forEach((run, i) => {
        const pred = run.prediction || "";
        const report = run.report || "";
        const content = pred + (report ? "\n\n" + report : "");
        state.currentProcess.rounds.push({
          round: i + 1,
          plan: "",
          report: content.trim() || `(Agent ${i + 1} 未返回)`,
          timestamp: event.timestamp || new Date().toISOString(),
        });
      });
      renderProcess();
      break;
    }

    case "complete": {
      // Web Weaver 完成事件
      const result = event.result || {};
      const answer = result.final_report || "";
      const lastAssistant = Array.from(messagesList.querySelectorAll('[data-role="assistant"]')).pop();
      if (lastAssistant && answer) {
        updateAssistantMessage(lastAssistant, answer, turnIndex);
      }
      if (answer) {
        state.conversationHistory.push({
          question: state.currentQuestion,
          answer: answer,
          timestamp: new Date().toISOString(),
        });
        if (state.currentSessionId) addToHistory();
      }
      if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
      }
      state.isResearching = false;
      updateButtonState(false);
      break;
    }

    case "final":
    case "summary": {
      const answer = event.answer || "";
      
      const lastAssistant = Array.from(messagesList.querySelectorAll('[data-role="assistant"]')).pop();
      if (lastAssistant) {
        updateAssistantMessage(lastAssistant, answer, turnIndex);
      }
      
      state.conversationHistory.push({
        question: state.currentQuestion,
        answer: answer,
        timestamp: new Date().toISOString(),
      });
      
      if (state.currentSessionId) {
        addToHistory();
      }
      
      if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
      }
      
      state.isResearching = false;
      updateButtonState(false);
      break;
    }

    case "turn_finished": {
      const finalAnswer = event.answer || "";
      
      const lastAssistant = Array.from(messagesList.querySelectorAll('[data-role="assistant"]')).pop();
      if (lastAssistant) {
        updateAssistantMessage(lastAssistant, finalAnswer, turnIndex);
      }
      
      state.conversationHistory.push({
        question: state.currentQuestion,
        answer: finalAnswer,
        timestamp: new Date().toISOString(),
      });
      
      if (state.currentSessionId) {
        addToHistory();
      }
      
      if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
      }
      
      state.isResearching = false;
      updateButtonState(false);
      break;
    }

    case "status": {
      // 记录 Web Weaver 阶段，用于 step 到 round 的映射
      if (event.phase) {
        state.webWeaverPhase = event.phase;
      }
      // 仅在明确表示终止时关闭流；"starting" 不应触发关闭（Web Weaver 每个阶段开始会发 starting）
      const terminalStatuses = ["completed", "failed", "timeout", "terminated", "answer found"];
      if (terminalStatuses.includes(event.status) && state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
        state.isResearching = false;
        updateButtonState(false);
      }
      break;
    }

    case "error": {
      const lastAssistant = Array.from(messagesList.querySelectorAll('[data-role="assistant"]')).pop();
      if (lastAssistant) {
        updateAssistantMessage(lastAssistant, `❌ ${event.message || "研究过程出错"}`);
      }
      
      if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
      }
      
      state.isResearching = false;
      updateButtonState(false);
      break;
    }
  }
};

// ============ API 交互 ============
const startResearch = async (evt) => {
  evt.preventDefault();
  
  const question = questionInput.value.trim();
  if (!question) return;
  
  // 如果正在研究，不允许提交新问题
  if (state.isResearching) {
    return;
  }
  
  // 立即清空输入框（在任何异步操作之前）
  questionInput.value = "";
  autoResizeTextarea(questionInput);
  
  state.currentQuestion = question;
  // 清空研究过程（新一轮研究）
  state.currentProcess.rounds = [];
  state.currentProcess.toolCalls = [];
  state.webWeaverPhase = "planner";
  
  // 清空右侧面板显示
  processContent.innerHTML = "";
  processContent.classList.add("hidden");
  processEmpty.classList.remove("hidden");
  
  state.isResearching = true;
  
  // 添加用户消息
  addUserMessage(question);
  
  // 添加助手加载消息
  addAssistantMessage("", true);
  
  // 更新按钮状态为中止图标
  updateButtonState(true);
  
  try {
    // 如果没有会话ID，先创建会话
    if (!state.currentSessionId) {
      const sessionPayload = {
        agent: state.settings.agent || "web_researcher",
        tts_num_agents: state.settings.ttsNumAgents ?? 3,
        max_turns: state.settings.maxTurns ?? 5,
      };
      if (state.settings.instruction) {
        sessionPayload.instruction = state.settings.instruction;
      }
      if (state.settings.tools.length > 0) {
        sessionPayload.tools = state.settings.tools;
      }
      
      const sessionResp = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sessionPayload),
      });
      
      if (!sessionResp.ok) {
        throw new Error("创建会话失败");
      }
      
      const sessionData = await sessionResp.json();
      state.currentSessionId = sessionData.session_id;
    }
    
    // 提交问题到会话
    const response = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.currentSessionId,
        question: question,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "提交问题失败");
    }
    
    // 开始 SSE 流
    openStream(state.currentSessionId);
    
  } catch (error) {
    console.error(error);
    const lastAssistant = Array.from(messagesList.querySelectorAll('[data-role="assistant"]')).pop();
    if (lastAssistant) {
      updateAssistantMessage(lastAssistant, `❌ ${error.message || "创建失败"}`);
    }
    state.isResearching = false;
    updateButtonState(false);
    // 确保输入框已清空（虽然前面已经清空了，但为了保险再次确认）
  }
};

// 更新按钮状态
const updateButtonState = (isResearching) => {
  if (isResearching) {
    // 显示中止图标（更大的方块）
    startButton.innerHTML = `
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <rect x="6" y="6" width="12" height="12" rx="2"/>
      </svg>
    `;
    startButton.title = "中止研究";
  } else {
    // 显示发送图标
    startButton.innerHTML = `
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7"/>
      </svg>
    `;
    startButton.title = "发送 (Ctrl+Enter)";
    startButton.disabled = false;
  }
};

// 中止研究
const stopResearch = async () => {
  // 先请求后端取消任务
  if (state.currentSessionId) {
    try {
      await fetch(`/api/session/${state.currentSessionId}/cancel`, { method: "POST" });
    } catch (err) {
      console.warn("取消请求失败", err);
    }
  }

  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }

  state.isResearching = false;
  updateButtonState(false);

  // 更新最后一条助手消息
  const lastAssistant = Array.from(messagesList.querySelectorAll('[data-role="assistant"]')).pop();
  if (lastAssistant && lastAssistant.querySelector(".animate-spin")) {
    updateAssistantMessage(lastAssistant, "⚠️ 研究已中止");
  }
};

const openStream = (sessionId) => {
  if (!sessionId) return;
  
  // 关闭旧的SSE连接
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
  
  // 创建新的SSE连接（每次都是新的连接）
  const source = new EventSource(`/api/session/${sessionId}/stream`);
  state.eventSource = source;
  
  source.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      processEvent(payload);
    } catch (error) {
      console.error("解析事件失败", error);
    }
  };
  
  source.onerror = (error) => {
    console.error("SSE 连接错误", error);
    // SSE错误时不要立即关闭，可能是网络抖动
  };
};

const fetchHistory = async () => {
  try {
    const response = await fetch("/api/history?limit=20");
    const data = await response.json();
    
    // 获取已删除的 ID 列表
    const deletedIds = JSON.parse(localStorage.getItem("deletedHistoryIds") || "[]");
    
    // 获取自定义标题
    const historyTitles = JSON.parse(localStorage.getItem("historyTitles") || "{}");
    
    // 过滤已删除的记录，并应用自定义标题
    const items = (data.items || [])
      .filter(item => {
        const id = item.session_id || item.task_id;
        return !deletedIds.includes(id);
      })
      .map(item => ({
        ...item,
        title: historyTitles[item.session_id || item.task_id] || null,
      }));
    
    renderHistory(items);
  } catch (error) {
    console.error("获取历史失败", error);
  }
};

const renderHistory = (items = []) => {
  if (!items.length) {
    historyEmpty.classList.remove("hidden");
    historyList.innerHTML = "";
    return;
  }
  
  historyEmpty.classList.add("hidden");
  historyList.innerHTML = items.map((item) => {
    // 会话模式：item 包含 session_id, turns 等
    const sessionId = item.session_id || item.task_id;  // 兼容旧格式
    const statusColor = item.status === "completed" || item.status === "active" ? "bg-green-500" : item.status === "failed" ? "bg-red-500" : "bg-gray-400";
    
    // 优先使用 first_question（会话模式）
    const firstQuestion = item.first_question || item.question || "";
    const turnCount = item.turn_count || (item.turns ? item.turns.length : 1);
    
    // 默认标题为第一个问题，如果超过10字符则截取前10字符
    const defaultTitle = firstQuestion ? (firstQuestion.length > 10 ? firstQuestion.slice(0, 10) : firstQuestion) : "新会话";
    const displayTitle = item.title || defaultTitle;
    
    // 显示轮次数
    const turnLabel = turnCount > 1 ? ` (${turnCount}轮)` : "";
    
    return `
      <div class="relative group history-item" data-session-id="${sessionId}">
        <button 
          data-session="${sessionId}" 
          class="w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 transition history-btn"
        >
          <div class="flex items-start gap-2">
            <span class="flex-shrink-0 w-1.5 h-1.5 ${statusColor} rounded-full mt-1.5"></span>
            <div class="flex-1 min-w-0">
              <p class="text-gray-900 line-clamp-2 group-hover:text-black history-title text-sm">${escapeHtml(displayTitle)}${turnLabel}</p>
              <p class="text-xs text-gray-400 mt-0.5">${formatDate(item.updated_at)}</p>
            </div>
          </div>
        </button>
        <div class="absolute right-1 top-1 opacity-0 group-hover:opacity-100 transition flex gap-1">
          <button 
            class="edit-history-btn p-1 bg-white hover:bg-gray-200 rounded border border-gray-300 shadow-sm"
            data-session-id="${sessionId}"
            data-title="${escapeHtml(displayTitle)}"
            title="编辑标题"
          >
            <svg class="w-3 h-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
            </svg>
          </button>
          <button 
            class="delete-history-btn p-1 bg-white hover:bg-red-50 rounded border border-gray-300 shadow-sm"
            data-session-id="${sessionId}"
            title="删除"
          >
            <svg class="w-3 h-3 text-gray-600 hover:text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>
    `;
  }).join("");
  
  // 绑定事件
  bindHistoryEvents();
};

// 绑定历史记录事件
const bindHistoryEvents = () => {
  // 回放会话
  historyList.querySelectorAll(".history-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sessionId = btn.dataset.session;
      replaySession(sessionId);
      closeMobilePanels(); // 移动端关闭侧边栏
    });
  });
  
  // 编辑标题
  historyList.querySelectorAll(".edit-history-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const sessionId = btn.dataset.sessionId;
      const currentTitle = btn.dataset.title;
      editHistoryTitle(sessionId, currentTitle);
    });
  });
  
  // 删除历史
  historyList.querySelectorAll(".delete-history-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const sessionId = btn.dataset.sessionId;
      deleteHistory(sessionId);
    });
  });
};

// 编辑标题
const editHistoryTitle = (sessionId, currentTitle) => {
  const newTitle = prompt("编辑标题:", currentTitle);
  if (newTitle === null || newTitle.trim() === currentTitle) return;
  
  // 保存到 localStorage
  const historyTitles = JSON.parse(localStorage.getItem("historyTitles") || "{}");
  historyTitles[sessionId] = newTitle.trim();
  localStorage.setItem("historyTitles", JSON.stringify(historyTitles));
  
  // 刷新列表
  fetchHistory();
};

// 删除历史记录
const deleteHistory = (sessionId) => {
  if (!confirm("确定要删除这条历史记录吗？")) return;
  
  // 从 localStorage 删除
  const deletedIds = JSON.parse(localStorage.getItem("deletedHistoryIds") || "[]");
  deletedIds.push(sessionId);
  localStorage.setItem("deletedHistoryIds", JSON.stringify(deletedIds));
  
  // 同时删除标题
  const historyTitles = JSON.parse(localStorage.getItem("historyTitles") || "{}");
  delete historyTitles[sessionId];
  localStorage.setItem("historyTitles", JSON.stringify(historyTitles));
  
  // 刷新列表
  fetchHistory();
};

const addToHistory = () => {
  // 刷新历史列表
  fetchHistory();
};

const replaySession = async (sessionId) => {
  if (!sessionId) return;
  
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
  
  // 清空当前对话
  messagesList.innerHTML = "";
  state.currentProcess.rounds = [];
  state.currentProcess.toolCalls = [];
  state.conversationHistory = [];
  
  // 清空研究过程面板
  processContent.innerHTML = "";
  processContent.classList.add("hidden");
  processEmpty.classList.remove("hidden");
  
  try {
    const response = await fetch(`/api/session/${sessionId}`);
    
    if (!response.ok) throw new Error("会话不存在");
    
    const session = await response.json();
    
    // 恢复会话ID
    state.currentSessionId = sessionId;
    
    // 显示所有轮次的对话
    if (session.turns && session.turns.length > 0) {
      for (let turnIdx = 0; turnIdx < session.turns.length; turnIdx++) {
        const turn = session.turns[turnIdx];
        
        // 添加用户消息
        addUserMessage(turn.question);
        
        // 添加助手消息（带 turnIndex，支持点击查看研究过程）
        addAssistantMessage(turn.answer || "研究中...", false, turnIdx);
        
        // 更新会话历史
        state.conversationHistory.push({
          question: turn.question,
          answer: turn.answer || "",
          timestamp: turn.created_at,
        });
      }
    }
    
  } catch (error) {
    console.error("加载会话失败:", error);
    alert(`加载失败: ${error.message}`);
  }
};

const resetResearch = () => {
  // 先中止当前研究
  if (state.isResearching) {
    stopResearch();
  }
  
  // 保存当前会话到历史（如果有对话记录）
  if (state.currentSessionId && state.conversationHistory.length > 0) {
    addToHistory();
  }
  
  // 清空对话
  messagesList.innerHTML = `
    <div id="welcomeSection" class="text-center py-12">
      <div class="inline-flex items-center justify-center w-12 h-12 bg-black rounded-full mb-4">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
      </div>
      <h2 class="text-xl font-medium text-gray-900 mb-2">深度研究</h2>
      <p class="text-sm text-gray-500">输入问题开始研究</p>
    </div>
  `;
  
  // 重置状态（开始新会话）
  state.currentSessionId = null;
  state.conversationHistory = [];
  state.currentProcess.rounds = [];
  state.currentProcess.toolCalls = [];
  state.isResearching = false;
  processContent.innerHTML = "";
  processContent.classList.add("hidden");
  processEmpty.classList.remove("hidden");
  
  questionInput.value = "";
  autoResizeTextarea(questionInput);
  updateButtonState(false);
  
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
};

// ============ 事件监听 ============
// 桌面端侧边栏控制
if (showSidebarBtn) showSidebarBtn.addEventListener("click", toggleSidebar);
if (toggleProcessBtn) toggleProcessBtn.addEventListener("click", toggleProcess);

// 移动端按钮
if (mobileMenuBtn) {
  mobileMenuBtn.addEventListener("click", () => {
    state.sidebarCollapsed = !state.sidebarCollapsed;
    toggleSidebar();
  });
}

if (mobileProcessBtn) {
  mobileProcessBtn.addEventListener("click", () => {
    state.processCollapsed = !state.processCollapsed;
    toggleProcess();
  });
}

// 遮罩层点击关闭
if (mobileOverlay) {
  mobileOverlay.addEventListener("click", closeMobilePanels);
}

// 新建研究
newResearchBtn.addEventListener("click", () => {
  resetResearch();
  closeMobilePanels(); // 移动端关闭侧边栏
});

// 表单提交事件：根据当前状态决定是提交还是中止
researchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  
  if (state.isResearching) {
    // 如果正在研究，则中止
    stopResearch();
  } else {
    // 否则开始新研究
    startResearch(e);
  }
});

questionInput.addEventListener("input", () => autoResizeTextarea(questionInput));
questionInput.addEventListener("keydown", (e) => {
  // Ctrl+Enter 或 Cmd+Enter 发送
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    researchForm.dispatchEvent(new Event("submit"));
  }
  // 单独的 Enter 换行（默认行为，不需要特殊处理）
});

settingsBtn.addEventListener("click", showSettings);
closeSettings.addEventListener("click", hideSettings);
cancelSettings.addEventListener("click", hideSettings);

saveSettings.addEventListener("click", () => {
  state.settings.agent = agentInput.value || "web_researcher";
  const n = parseInt(ttsNumAgentsInput.value, 10);
  state.settings.ttsNumAgents = (n >= 2 && n <= 8) ? n : 3;
  const mt = parseInt(maxTurnsInput.value, 10);
  state.settings.maxTurns = (mt >= 1 && mt <= 20) ? mt : 5;
  state.settings.instruction = instructionInput.value.trim();
  state.settings.tools = parseTools(toolsInput.value);
  hideSettings();
});

// 历史记录的点击事件由 bindHistoryEvents() 动态绑定

settingsModal.addEventListener("click", (e) => {
  if (e.target === settingsModal) {
    hideSettings();
  }
});

// 窗口大小变化监听
window.addEventListener("resize", () => {
  const wasMobile = state.isMobile;
  const nowMobile = checkMobile();
  
  // 从桌面切换到移动端
  if (!wasMobile && nowMobile) {
    closeMobilePanels();
  }
  // 从移动端切换到桌面端
  else if (wasMobile && !nowMobile) {
    // 清理移动端样式
    historySidebar.classList.remove("mobile-open");
    processSidebar.classList.remove("mobile-open");
    mobileOverlay.classList.remove("active");
    
    // 恢复桌面端默认状态
    if (!state.sidebarCollapsed) {
      historySidebar.style.transform = "translateX(0)";
      mainContent.style.marginLeft = "260px";
    }
    if (!state.processCollapsed) {
      processSidebar.style.width = "480px";
      processSidebar.style.transform = "translateX(0)";
    }
  }
});

// ============ 初始化 ============
checkMobile(); // 初始化移动端状态
fetchHistory();
autoResizeTextarea(questionInput);

// 移动端初始化：默认折叠所有侧边栏
if (state.isMobile) {
  state.sidebarCollapsed = true;
  state.processCollapsed = true;
} else {
  // 桌面端初始化：设置按钮的初始箭头方向
  // 历史记录侧边栏初始是展开的（sidebarCollapsed = false），所以箭头应该向左（表示可以隐藏）
  if (showSidebarBtn) {
    showSidebarBtn.querySelector("svg path").setAttribute("d", "M15 19l-7-7 7-7");
    showSidebarBtn.title = "隐藏历史记录";
  }
  
  // 研究过程侧边栏初始也是展开的（processCollapsed = false），所以箭头应该向右（表示可以隐藏）
  if (processIcon) {
    processIcon.querySelector("path").setAttribute("d", "M9 5l7 7-7 7");
    toggleProcessBtn.title = "隐藏研究过程";
  }
}
