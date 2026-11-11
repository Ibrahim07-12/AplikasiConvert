const FORMAT_MAPPING = {
  jpg: ["png", "webp", "pdf", "svg"], jpeg: ["png", "webp", "pdf", "svg"],
  png: ["jpg", "webp", "pdf", "svg"], webp: ["jpg", "png", "pdf", "svg"],
  svg: ["png", "jpg", "pdf"], pdf: ["jpg", "png", "docx", "xlsx", "pptx"],
  docx: ["pdf", "jpg", "png"], doc: ["pdf", "jpg", "png"],
  xlsx: ["pdf", "csv", "jpg"], xls: ["pdf", "csv", "jpg"],
  pptx: ["pdf", "jpg", "png", "docx"], ppt: ["pdf", "docx", "jpg", "png"],
  html: ["pdf", "jpg", "png"], htm: ["pdf", "jpg", "png"],
};

const TOOL_MAPPING = {
  image: ["convert", "compress", "resize", "crop", "rotate", "flip", "grayscale", "watermark", "remove-bg"],
  pdf: ["convert", "merge", "split", "remove-pages", "rotate-pages", "compress", "to-images", "add-page-numbers", "extract-text", "protect"],
  word: ["convert", "compress", "merge", "extract-images"],
  excel: ["convert", "compress"],
  ppt: ["convert", "compress", "merge", "extract-images"],
  html: ["convert", "minify", "screenshot"],
};

const TOOL_LABELS = {
  convert: "Convert", compress: "Compress", resize: "Resize", crop: "Crop",
  rotate: "Rotate", flip: "Flip", grayscale: "Grayscale", watermark: "Watermark",
  "remove-bg": "Remove BG", merge: "Merge", split: "Split", "remove-pages": "Remove Pages",
  "rotate-pages": "Rotate Pages", "to-images": "To Images", "add-page-numbers": "Page Numbers",
  "extract-text": "Extract Text", protect: "Protect", "extract-images": "Extract Images",
  minify: "Minify", screenshot: "Screenshot",
};

function getFileCategory(extension) {
  const ext = extension.toLowerCase();
  if (["jpg", "jpeg", "png", "webp", "svg"].includes(ext)) return "image";
  if (ext === "pdf") return "pdf";
  if (["docx", "doc"].includes(ext)) return "word";
  if (["xlsx", "xls", "csv"].includes(ext)) return "excel";
  if (["pptx", "ppt"].includes(ext)) return "ppt";
  if (["html", "htm"].includes(ext)) return "html";
  return "unknown";
}

const fileInput = document.querySelector("#file-input");
const dropZone = document.querySelector("#drop-zone");
const fileList = document.querySelector("#file-list");
const toolGrid = document.querySelector("#tool-grid");
const dynamicTool = document.querySelector("#dynamic-tool");
const toolTitle = document.querySelector("#tool-title");
const toolControls = document.querySelector("#tool-controls");
const runTool = document.querySelector("#run-tool");
const progressBar = document.querySelector("#progress-bar");
const statusMessage = document.querySelector("#status");
const categoryLabel = document.querySelector("#category-label");
let selectedFiles = [];
let selectedTool = null;
let currentCategory = "unknown";

const extensionOf = (name) => name.split(".").pop().toLowerCase();
const setStatus = (message, type = "") => {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
};
const makeLabel = (value) => TOOL_LABELS[value] || value.replaceAll("-", " ");

function renderFiles() {
  fileList.replaceChildren();
  if (!selectedFiles.length) {
    fileList.innerHTML = '<p class="empty-state">No files selected</p>';
    return;
  }
  selectedFiles.forEach((file, index) => {
    const row = document.createElement("div");
    row.className = "file-row";
    row.innerHTML = '<span class="file-type">FILE</span><span class="file-info"><b></b><small></small></span><button type="button" aria-label="Remove file">×</button>';
    row.querySelector("b").textContent = file.name;
    row.querySelector("small").textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
    row.querySelector("button").addEventListener("click", () => {
      selectedFiles.splice(index, 1);
      resetTools();
      renderFiles();
      if (selectedFiles.length) renderTools();
    });
    fileList.append(row);
  });
}

function renderTools() {
  toolGrid.replaceChildren();
  categoryLabel.textContent = currentCategory.toUpperCase();
  (TOOL_MAPPING[currentCategory] || []).forEach((tool) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "tool-card";
    card.dataset.tool = tool;
    card.innerHTML = `<strong>${makeLabel(tool)}</strong><small>${tool === "convert" ? "Change format" : "Open tool"}</small>`;
    card.addEventListener("click", () => selectTool(tool, card));
    toolGrid.append(card);
  });
  if (!toolGrid.children.length) {
    toolGrid.innerHTML = '<p class="empty-state">No tools available for this file type.</p>';
  }
}

function resetTools() {
  selectedTool = null;
  dynamicTool.hidden = true;
  runTool.disabled = true;
  toolControls.replaceChildren();
  document.querySelectorAll(".tool-card").forEach((card) => card.classList.remove("selected"));
}

function selectTool(tool, card) {
  selectedTool = tool;
  document.querySelectorAll(".tool-card").forEach((item) => item.classList.remove("selected"));
  card.classList.add("selected");
  dynamicTool.hidden = false;
  toolTitle.textContent = `${makeLabel(tool).toUpperCase()} SETTINGS`;
  toolControls.replaceChildren();
  runTool.disabled = !["convert", "compress"].includes(tool);
  if (tool === "convert") {
    const select = document.createElement("select");
    select.id = "target-format";
    const targets = FORMAT_MAPPING[extensionOf(selectedFiles[0].name)] || [];
    targets.forEach((target) => select.add(new Option(target.toUpperCase(), target)));
    toolControls.append(labelledControl("Target format", select));
    runTool.disabled = !targets.length;
  } else if (tool === "compress") {
    const range = document.createElement("input");
    range.type = "range"; range.min = "1"; range.max = "100"; range.value = "75";
    const value = document.createElement("span");
    value.className = "range-value"; value.textContent = "75";
    range.addEventListener("input", () => { value.textContent = range.value; });
    const wrapper = labelledControl("Quality", range);
    wrapper.append(value);
    toolControls.append(wrapper);
  } else if (tool === "crop") {
    toolControls.innerHTML = '<div class="placeholder">Canvas crop editor will be available in the next tool iteration.</div>';
  } else {
    toolControls.innerHTML = `<div class="placeholder">${makeLabel(tool)} is mapped and ready for a future backend handler.</div>`;
  }
}

function labelledControl(label, control) {
  const wrapper = document.createElement("div");
  wrapper.className = "tool-control";
  const text = document.createElement("label");
  text.textContent = label;
  wrapper.append(text, control);
  return wrapper;
}

function selectFiles(files) {
  selectedFiles = [...files].filter((file) => file.size <= 25 * 1024 * 1024);
  if (!selectedFiles.length) {
    setStatus("Select a file up to 25 MB.", "error");
    resetTools(); renderFiles(); return;
  }
  if (selectedFiles.length !== files.length) setStatus("Files above 25 MB were ignored.", "error");
  else setStatus("");
  currentCategory = getFileCategory(extensionOf(selectedFiles[0].name));
  resetTools(); renderFiles(); renderTools();
}

fileInput.addEventListener("change", () => selectFiles(fileInput.files));
["dragenter", "dragover"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => {
  event.preventDefault(); dropZone.classList.add("is-dragging");
}));
["dragleave", "drop"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => {
  event.preventDefault(); dropZone.classList.remove("is-dragging");
}));
dropZone.addEventListener("drop", (event) => selectFiles(event.dataTransfer.files));

runTool.addEventListener("click", async () => {
  if (!selectedFiles.length || !selectedTool) return;
  const formData = new FormData();
  selectedFiles.forEach((file) => formData.append("files", file));
  let endpoint = "/convert/batch";
  if (selectedTool === "compress") {
    endpoint = "/tools/image/compress";
    formData.delete("files"); formData.append("file", selectedFiles[0]);
    formData.append("quality", toolControls.querySelector("input").value);
  } else {
    formData.append("target_format", toolControls.querySelector("select").value);
  }
  if (selectedFiles.length === 1 && selectedTool === "convert") {
    endpoint = "/convert"; formData.delete("files"); formData.append("file", selectedFiles[0]);
  }
  runTool.disabled = true; progressBar.style.width = "25%"; setStatus("Processing...");
  try {
    const response = await fetch(endpoint, { method: "POST", body: formData });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "The operation failed.");
    }
    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = selectedTool === "compress" ? `${selectedFiles[0].name}-compressed` : "flux-output";
    link.click(); URL.revokeObjectURL(link.href);
    progressBar.style.width = "100%"; setStatus("Done. Download started.", "success");
  } catch (error) {
    progressBar.style.width = "0"; setStatus(error.message, "error");
  } finally { runTool.disabled = false; }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !runTool.disabled && event.target.tagName !== "SELECT") runTool.click();
});
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
