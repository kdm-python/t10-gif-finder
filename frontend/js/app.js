import { getMedia, getTags, getStreams, sendMedia } from "./api.js";

const mediaDisplay = document.getElementById("media-display");
const tagsDisplay = document.getElementById("tags-display");
const streamsDisplay = document.getElementById("streams-display");

async function renderMedia() {
  const media = await getMedia();

  mediaDisplay.innerHTML = "";

  for (const item of media) {
    const element = document.createElement("p");
    element.innerText = `${item.original_filename} | ${JSON.stringify(item.tags)}`;
    mediaDisplay.append(element);
  }
}

function setupUploadForm() {
  const form = document.getElementById("upload-form");

  form.addEventListener("submit", handleUpload);
}

async function handleUpload(event) {
  event.preventDefault();

  const fileInput = document.getElementById("media-file");
  const tagsInput = document.getElementById("media-tags");
  const streamInput = document.getElementById("stream-id").value;
  const authorInput = document.getElementById("author").value;
  const title = document.getElementById("title").value;
  const description = document.getElementById("description").value;
  const sourceUrl = document.getElementById("source-url").value;

  const tags = tagsInput.value
    .split(",")
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  for (const tag of tags) {
    formData.append("tags", tag);
  }

  if (authorInput) formData.append("author", authorInput);
  if (streamInput) formData.append("stream_id", streamInput);
  if (title) formData.append("title", title);
  if (description) formData.append("description", description);
  if (sourceUrl) formData.append("source_url", sourceUrl);

  for (const [key, value] of formData.entries()) {
    console.log(key, value);
  }
  await sendMedia(formData);

  await Promise.all([renderMedia(), renderTags()]);
}

async function renderTags() {
  const tags = await getTags();

  tagsDisplay.innerHTML = "";

  for (const tag of tags) {
    const element = document.createElement("p");
    element.innerText = tag.name;
    tagsDisplay.append(element);
  }
}

async function renderStreams() {
  let streams = await getStreams();

  streamsDisplay.innerHTML = "";

  // sort by date key descending
  streams = streams.sort((a, b) => new Date(b.date) - new Date(a.date));

  for (const stream of streams.slice(1, 10)) {
    const element = document.createElement("p");
    element.innerText = JSON.stringify(stream);
    streamsDisplay.append(element);
  }
}

async function main() {
  renderMedia();
  renderTags();
  renderStreams();
  setupUploadForm();
}

main();
