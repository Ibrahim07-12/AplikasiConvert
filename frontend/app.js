const fileInput = document.querySelector("#file-input");
const dropZone = document.querySelector("#drop-zone");
const fileList = document.querySelector("#file-list");
const targetFormat = document.querySelector("#target-format");
const convertButton = document.querySelector("#convert-button");
const progressBar = document.querySelector("#progress-bar");
const statusMessage = document.querySelector("#status");
const installButton = document.querySelector("#install-button");
let selectedFiles = [];
let categories = {};
let deferredInstallPrompt;

const extensionOf = (name) => name.split(".").pop().toLowerCase();
const normalizedExtensionOf = (name) => extensionOf(name);
const setStatus = (message, type = "") => {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
};

const renderFiles = () => {
  fileList.replaceChildren();
  if (!selectedFiles.length) {
    fileList.innerHTML = '<div class="empty-state">No files selected</div>';
    return;
  }
  selectedFiles.forEach((file, index) => {
    const row = document.createElement("div");
    row.className = "file-row";
    row.innerHTML = `<span class="file-type">FILE</span><span class="file-info"><b></b><small></small></span><button type="button" aria-label="Remove file">×</button>`;
    row.querySelector("b").textContent = file.name;
    row.querySelector("small").textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
    row.querySelector("button").addEventListener("click", () => {
      selectedFiles.splice(index, 1);
      updateFormats();
      renderFiles();
    });
    fileList.append(row);
  });
};

const updateFormats = () => {
  targetFormat.replaceChildren();
  const extensions = selectedFiles.map((file) => normalizedExtensionOf(file.name));
  const formatSets = extensions.map((extension) => categories[extension] || []);
  const formats = formatSets.length
    ? formatSets.reduce((common, current) => common.filter((format) => current.includes(format)))
    : [];
  formats.forEach((format) => {
    const option = new Option(format.toUpperCase(), format);
    targetFormat.append(option);
  });
  targetFormat.disabled = !formats.length;
  convertButton.disabled = !selectedFiles.length || !formats.length;
  if (selectedFiles.length && !formats.length) setStatus("Format sumber belum didukung.", "error");
};

const selectFiles = (files) => {
  selectedFiles = [...files].filter((file) => file.size <= 25 * 1024 * 1024);
  if (selectedFiles.length !== files.length) setStatus("File di atas 25 MB diabaikan.", "error");
  else setStatus("");
  renderFiles();
  updateFormats();
};

fileInput.addEventListener("change", () => selectFiles(fileInput.files));
["dragenter", "dragover"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropZone.classList.add("is-dragging");
}));
["dragleave", "drop"].forEach((eventName) => dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropZone.classList.remove("is-dragging");
}));
dropZone.addEventListener("drop", (event) => selectFiles(event.dataTransfer.files));

convertButton.addEventListener("click", async () => {
  if (!selectedFiles.length) return;
  convertButton.disabled = true;
  progressBar.style.width = "20%";
  setStatus("Converting...");
  const formData = new FormData();
  selectedFiles.forEach((file) => formData.append("files", file));
  formData.append("target_format", targetFormat.value);
  const endpoint = selectedFiles.length === 1 ? "/convert" : "/convert/batch";
  if (selectedFiles.length === 1) {
    formData.delete("files");
    formData.append("file", selectedFiles[0]);
  }
  try {
    const response = await fetch(endpoint, { method: "POST", body: formData });
    progressBar.style.width = "75%";
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Conversion failed.");
    }
    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = selectedFiles.length === 1
      ? `${selectedFiles[0].name.split(".").slice(0, -1).join(".") || "converted"}.${targetFormat.value}`
      : "converted-files.zip";
    link.click();
    URL.revokeObjectURL(link.href);
    progressBar.style.width = "100%";
    setStatus("Conversion complete. Download started.", "success");
  } catch (error) {
    progressBar.style.width = "0";
    setStatus(error.message, "error");
  } finally {
    convertButton.disabled = false;
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !convertButton.disabled && event.target.tagName !== "SELECT") convertButton.click();
});
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  installButton.hidden = false;
});
installButton.addEventListener("click", async () => {
  if (!deferredInstallPrompt) return;
  deferredInstallPrompt.prompt();
  deferredInstallPrompt = null;
  installButton.hidden = true;
});

fetch("/supported-formats")
  .then((response) => response.json())
  .then((data) => {
    categories = {
      ...data.mapping,
    };
  })
  .catch(() => setStatus("Could not load supported formats.", "error"));

if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
