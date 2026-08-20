const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const stateButton = document.querySelector("#state-button");
const resetButton = document.querySelector("#reset-button");
const statePanel = document.querySelector("#state-panel");
const stateOutput = document.querySelector("#state-output");
const status = document.querySelector("#status");

function appendMessage(role, text, toolSteps = []) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const label = document.createElement("span");
  label.className = "label";
  label.textContent = role === "user" ? "你" : role === "error" ? "错误" : "助手";

  const content = document.createElement("p");
  content.textContent = text;

  article.append(label, content);

  for (const step of toolSteps) {
    const detail = document.createElement("div");
    detail.className = "tool-step";
    detail.textContent = `${step.tool_name}: ${JSON.stringify(step.result)}`;
    article.append(detail);
  }

  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }

  return payload;
}

function setBusy(busy) {
  sendButton.disabled = busy;
  input.disabled = busy;
  status.textContent = busy ? "处理中" : "就绪";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();

  if (!message) {
    return;
  }

  appendMessage("user", message);
  input.value = "";
  setBusy(true);

  try {
    const payload = await request("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message}),
    });
    appendMessage("assistant", payload.answer, payload.tool_steps);
  } catch (error) {
    appendMessage("error", error.message);
  } finally {
    setBusy(false);
    input.focus();
  }
});

stateButton.addEventListener("click", async () => {
  try {
    const payload = await request("/api/state");
    stateOutput.textContent = JSON.stringify(payload, null, 2);
    statePanel.open = true;
  } catch (error) {
    appendMessage("error", error.message);
  }
});

resetButton.addEventListener("click", async () => {
  try {
    const payload = await request("/api/reset", {method: "POST"});
    stateOutput.textContent = JSON.stringify(payload, null, 2);
    messages.replaceChildren();
    appendMessage("assistant", "会话已重置，请输入新的任务。");
  } catch (error) {
    appendMessage("error", error.message);
  }
});
