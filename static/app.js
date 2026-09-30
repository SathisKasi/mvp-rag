const fileInput = document.querySelector("#pdf-input");
const uploadTrigger = document.querySelector("#upload-trigger");
const uploadStatus = document.querySelector("#upload-status");
const documentList = document.querySelector("#document-list");
const emptyLibrary = document.querySelector("#empty-library");
const documentCount = document.querySelector("#document-count");
const conversation = document.querySelector("#conversation");
const welcome = document.querySelector("#welcome");
const chatForm = document.querySelector("#chat-form");
const questionInput = document.querySelector("#question-input");
const sendButton = document.querySelector("#send-button");
const toast = document.querySelector("#toast");
const uploadedFiles = new Map();
let isSending = false;
let toastTimer;

function showStatus(message, isError = false) {
  uploadStatus.textContent = message;
  uploadStatus.classList.toggle("error", isError);
  uploadStatus.hidden = false;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 2800);
}

function addDocument({ id, filename, pages, chunks }) {
  const key = id || filename;
  if (uploadedFiles.has(key)) {
    uploadedFiles.set(key, { pages, chunks });
    const existing = [...documentList.querySelectorAll(".document-item")]
      .find((item) => item.dataset.documentId === key);
    if (existing) existing.remove();
  } else {
    uploadedFiles.set(key, { pages, chunks });
  }

  emptyLibrary.hidden = true;
  const item = document.createElement("div");
  item.className = "document-item";
  item.dataset.documentId = key;

  const badge = document.createElement("span");
  badge.className = "pdf-mark";
  badge.textContent = "PDF";
  badge.setAttribute("aria-hidden", "true");

  const meta = document.createElement("span");
  meta.className = "document-meta";
  const name = document.createElement("strong");
  name.title = filename;
  name.textContent = filename;
  const detail = document.createElement("span");
  detail.textContent = `${pages} ${pages === 1 ? "page" : "pages"} | ${chunks} text chunks`;
  meta.append(name, detail);
  const deleteButton = document.createElement("button");
  deleteButton.className = "delete-document-button";
  deleteButton.type = "button";
  deleteButton.title = `Delete ${filename} from PostgreSQL`;
  deleteButton.setAttribute("aria-label", `Delete ${filename}`);
  deleteButton.innerHTML = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4.5 6h11M8 6V4.5h4V6m2.5 0-.6 9.2a1 1 0 0 1-1 .8H7.1a1 1 0 0 1-1-.8L5.5 6m3 3v4m3-4v4"/></svg>';
  deleteButton.addEventListener("click", () => deleteDocument(key, filename, item, deleteButton));
  item.append(badge, meta, deleteButton);
  documentList.prepend(item);
  documentCount.textContent = String(uploadedFiles.size);
}

async function loadDocuments() {
  const response = await fetch("/api/documents");
  const result = await readApiResponse(response, "Could not load saved documents.");
  if (!Array.isArray(result.documents)) throw new Error("The server returned an invalid document list.");
  emptyLibrary.hidden = result.documents.length > 0;
  for (const document of result.documents) {
    if (typeof document.id === "string" && typeof document.filename === "string") {
      addDocument(document);
    }
  }
}

async function deleteDocument(id, filename, element, button) {
  if (!window.confirm(`Delete ${filename} and its vectors from PostgreSQL? This cannot be undone.`)) return;

  button.disabled = true;
  try {
    const response = await fetch(`/api/documents/${encodeURIComponent(id)}`, { method: "DELETE" });
    await readApiResponse(response, `Could not delete ${filename}.`);
    uploadedFiles.delete(id);
    element.remove();
    documentCount.textContent = String(uploadedFiles.size);
    emptyLibrary.hidden = uploadedFiles.size > 0;
    showStatus(`${filename} and its indexed vectors were deleted.`);
  } catch (error) {
    showStatus(error.message || `Could not delete ${filename}.`, true);
    button.disabled = false;
  }
}

async function uploadFile(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showStatus(`${file.name} is not a PDF. Choose a .pdf file.`, true);
    return;
  }
  if (file.size === 0) {
    showStatus(`${file.name} is empty. Choose a different PDF.`, true);
    return;
  }
  if (file.size > 25 * 1024 * 1024) {
    showStatus(`${file.name} is larger than 25 MB.`, true);
    return;
  }

  uploadTrigger.disabled = true;
  uploadTrigger.querySelector(".upload-copy strong").textContent = "Adding PDF...";
  showStatus(`Reading ${file.name} and adding its text to Chroma...`);
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload", { method: "POST", body: formData });
    const result = await readApiResponse(response, "The PDF could not be added.");
    if (typeof result.filename !== "string" || !Number.isFinite(result.pages) || !Number.isFinite(result.chunks)) {
      throw new Error("The server returned an invalid upload response.");
    }
    if (result.duplicate) {
      if (typeof result.id === "string" && !uploadedFiles.has(result.id)) addDocument(result);
      showStatus(`${result.filename} is already in PostgreSQL. No duplicate chunks were added.`);
      showToast("Duplicate PDF skipped");
      return;
    }
    addDocument(result);
    showStatus(`${result.filename} is ready. Added ${result.inserted_chunks ?? result.chunks} text chunks from ${result.pages} pages.`);
    showToast("PDF added to your knowledge base");
  } catch (error) {
    showStatus(error.message || "Upload failed. Check the server and try again.", true);
  } finally {
    uploadTrigger.disabled = false;
    uploadTrigger.querySelector(".upload-copy strong").textContent = "Add a PDF";
    fileInput.value = "";
  }
}

async function readApiResponse(response, fallbackMessage) {
  let result = {};
  try {
    result = await response.json();
  } catch {
    throw new Error(fallbackMessage);
  }
  if (!result || typeof result !== "object" || Array.isArray(result)) throw new Error(fallbackMessage);
  if (!response.ok) {
    const detail = typeof result.detail === "string" ? result.detail : fallbackMessage;
    throw new Error(detail);
  }
  return result;
}

function makeMessage(role, text, sources = []) {
  const row = document.createElement("article");
  row.className = `message ${role}`;

  if (role === "assistant") {
    const avatar = document.createElement("span");
    avatar.className = "message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.innerHTML = '<svg viewBox="0 0 24 24" fill="none"><path d="M6 4.75h8l4 4V19H6V4.75Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M14 5v4h4M9 13h6M9 16h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';
    row.append(avatar);
  }

  const body = document.createElement("div");
  body.className = "message-body";
  const label = document.createElement("p");
  label.className = "message-label";
  label.textContent = role === "user" ? "YOU" : "SATHIS RAG";
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;
  body.append(label, bubble);

  if (sources.length) {
    const sourceList = document.createElement("div");
    sourceList.className = "source-list";
    for (const source of sources) {
      const chip = document.createElement("span");
      chip.className = "source-chip";
      const file = document.createElement("strong");
      file.textContent = source.filename;
      file.title = source.filename;
      chip.append(file);
      if (source.page) chip.append(document.createTextNode(` | p. ${source.page}`));
      sourceList.append(chip);
    }
    body.append(sourceList);
  }

  row.append(body);
  return row;
}

function addTypingIndicator() {
  const row = document.createElement("article");
  row.className = "message assistant";
  row.id = "typing-indicator";
  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.textContent = "B";
  avatar.setAttribute("aria-hidden", "true");
  const body = document.createElement("div");
  body.className = "message-body";
  const label = document.createElement("p");
  label.className = "message-label";
  label.textContent = "SEARCHING YOUR DOCUMENTS";
  const dots = document.createElement("div");
  dots.className = "message-bubble typing";
  dots.setAttribute("aria-label", "Assistant is responding");
  dots.innerHTML = "<span></span><span></span><span></span>";
  body.append(label, dots);
  row.append(avatar, body);
  conversation.append(row);
  conversation.scrollTop = conversation.scrollHeight;
}

async function askQuestion(question) {
  const cleaned = question.trim();
  if (!cleaned || isSending) return;

  welcome.hidden = true;
  conversation.append(makeMessage("user", cleaned));
  questionInput.value = "";
  questionInput.style.height = "auto";
  isSending = true;
  sendButton.disabled = true;
  addTypingIndicator();
  conversation.scrollTop = conversation.scrollHeight;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: cleaned }),
    });
    const result = await readApiResponse(response, "The answer could not be generated.");
    if (
      typeof result.answer !== "string"
      || !Array.isArray(result.sources)
      || !result.sources.every((source) => source && typeof source.filename === "string")
    ) {
      throw new Error("The server returned an invalid chat response.");
    }
    document.querySelector("#typing-indicator")?.remove();
    conversation.append(makeMessage("assistant", result.answer, result.sources || []));
  } catch (error) {
    document.querySelector("#typing-indicator")?.remove();
    conversation.append(makeMessage("assistant", error.message || "Something went wrong. Check that the app is running and try again."));
  } finally {
    isSending = false;
    sendButton.disabled = false;
    questionInput.focus();
    conversation.scrollTop = conversation.scrollHeight;
  }
}

uploadTrigger.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", async () => {
  for (const file of Array.from(fileInput.files || [])) {
    await uploadFile(file);
  }
});

for (const eventName of ["dragenter", "dragover"]) {
  uploadTrigger.addEventListener(eventName, (event) => {
    event.preventDefault();
    uploadTrigger.classList.add("is-dragging");
  });
}
for (const eventName of ["dragleave", "drop"]) {
  uploadTrigger.addEventListener(eventName, (event) => {
    event.preventDefault();
    uploadTrigger.classList.remove("is-dragging");
  });
}
uploadTrigger.addEventListener("drop", (event) => {
  for (const file of Array.from(event.dataTransfer?.files || [])) {
    uploadFile(file);
  }
});

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion(questionInput.value);
});
questionInput.addEventListener("input", () => {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 120)}px`;
});
questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => askQuestion(button.dataset.question));
});

document.querySelector("#new-chat").addEventListener("click", () => {
  conversation.replaceChildren(welcome);
  welcome.hidden = false;
  questionInput.value = "";
  questionInput.focus();
});

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    document.querySelector("#new-chat").click();
  }
});

loadDocuments().catch((error) => {
  showStatus(error.message || "Could not load saved documents.", true);
});
