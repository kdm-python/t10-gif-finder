import { getMedia, getTags, getStreams, sendMedia } from "./api.js";

const mediaDisplay = document.getElementById("media-display");
const tagsDisplay = document.getElementById("tags-display");
const streamsDisplay = document.getElementById("streams-display");
const status = document.getElementById("upload-status");

const textCell = (value) => {
  const cell = document.createElement("td");
  cell.textContent = value ?? "—";
  return cell;
};

function tagCell(tags) {
  const cell = document.createElement("td");
  const list = document.createElement("div");
  list.className = "tag-list";
  tags.forEach((tag) => {
    const badge = document.createElement("span");
    badge.className = "tag";
    badge.textContent = tag;
    list.append(badge);
  });
  cell.append(list);
  return cell;
}

async function renderMedia() {
  const media = await getMedia();
  mediaDisplay.replaceChildren();
  media.forEach((item) => {
    const row = document.createElement("tr");
    row.append(
      textCell(item.original_filename),
      tagCell(item.tags),
      textCell(item.author),
      textCell(item.stream_id),
    );
    mediaDisplay.append(row);
  });
  document.getElementById("media-count").textContent =
    `${media.length} item${media.length === 1 ? "" : "s"}`;
}

async function renderTags() {
  const tags = await getTags();
  tagsDisplay.replaceChildren();
  tags.forEach((tag) => {
    const row = document.createElement("tr");
    row.append(
      textCell(tag.id),
      textCell(tag.name),
      textCell(new Date(tag.created_at).toLocaleDateString()),
    );
    tagsDisplay.append(row);
  });
  document.getElementById("tag-count").textContent = `${tags.length} total`;
}

async function renderStreams() {
  const streams = await getStreams();
  streams.sort((a, b) => b.stream_date.localeCompare(a.stream_date));
  streamsDisplay.replaceChildren();
  streams.forEach((stream) => {
    const row = document.createElement("tr");
    row.append(
      textCell(stream.id),
      textCell(stream.stream_date),
      textCell(stream.description),
    );
    streamsDisplay.append(row);
  });
  document.getElementById("stream-count").textContent =
    `${streams.length} total`;
}

function setStatus(message, kind = "") {
  status.textContent = message;
  status.className = kind;
}

async function handleUpload(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const file = document.getElementById("media-file").files[0];
  const tags = document
    .getElementById("media-tags")
    .value.split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);

  if (!file || !tags.length) {
    setStatus("Choose a file and at least one tag.", "error");
    return;
  }

  const submit = form.querySelector("button[type=submit]");
  const formData = new FormData();

  formData.append("file", file);
  tags.forEach((tag) => formData.append("tags", tag));
  [
    ["author", "author"],
    ["stream_id", "stream-id"],
    ["title", "title"],
    ["description", "description"],
    ["source_url", "source-url"],
  ].forEach(([key, id]) => {
    const value = document.getElementById(id).value.trim();
    if (value) formData.append(key, value);
  });

  try {
    submit.disabled = true;
    setStatus(`Uploading ${file.name}…`);
    const created = await sendMedia(formData);
    console.log("[gif-finder] media uploaded", created);
    form.reset();
    setStatus(`Uploaded ${created.original_filename}.`, "success");
    await Promise.all([renderMedia(), renderTags(), renderStreams()]);
  } catch (error) {
    console.error("[gif-finder] upload failed", error);
    setStatus(`Upload failed: ${error.message}`, "error");
  } finally {
    submit.disabled = false;
  }
}

async function main() {
  document
    .getElementById("upload-form")
    .addEventListener("submit", handleUpload);
  try {
    await Promise.all([renderMedia(), renderTags(), renderStreams()]);
    console.log("[gif-finder] upload page ready");
  } catch (error) {
    console.error("[gif-finder] could not load upload page data", error);
    setStatus(`Could not load catalogue data: ${error.message}`, "error");
  }
}

main();
