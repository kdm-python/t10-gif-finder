import { getMedia, mediaPreviewUrl } from "./api.js";

const grid = document.getElementById("gif-grid");
const summary = document.getElementById("filter-summary");
const dialog = document.getElementById("media-dialog");
const details = document.getElementById("media-details");

let media = [];
const filters = {
  tag: document.getElementById("tag-filter"),
  author: document.getElementById("author-filter"),
  stream: document.getElementById("stream-filter"),
};

function addOptions(select, values) {
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  });
}

function populateFilters() {
  addOptions(
    filters.tag,
    [...new Set(media.flatMap((item) => item.tags))].sort(),
  );

  addOptions(
    filters.author,
    [...new Set(media.map((item) => item.author).filter(Boolean))].sort(
      (a, b) => a.localeCompare(b),
    ),
  );

  addOptions(
    filters.stream,
    [
      ...new Set(
        media.map((item) => item.stream_id).filter((id) => id !== null),
      ),
    ].sort((a, b) => a - b),
  );
}

function matchingMedia() {
  return media.filter(
    (item) =>
      (!filters.tag.value || item.tags.includes(filters.tag.value)) &&
      (!filters.author.value || item.author === filters.author.value) &&
      (!filters.stream.value ||
        String(item.stream_id) === filters.stream.value),
  );
}

function showDetails(item) {
  document.getElementById("media-dialog-title").textContent =
    item.original_filename;
  details.replaceChildren();

  Object.entries(item).forEach(([key, value]) => {
    const term = document.createElement("dt");
    term.textContent = key.replaceAll("_", " ");
    const definition = document.createElement("dd");
    definition.textContent = Array.isArray(value)
      ? value.join(", ")
      : value === null
        ? "—"
        : String(value);
    details.append(term, definition);
  });

  dialog.showModal();
}

function renderGrid() {
  const results = matchingMedia();
  grid.replaceChildren();
  summary.textContent = `${results.length} of ${media.length} media item${media.length === 1 ? "" : "s"}`;

  if (!results.length) {
    grid.innerHTML =
      '<div class="empty-state">No media matches those filters.</div>';
    return;
  }

  results.forEach((item) => {
    const card = document.createElement("article");
    card.className = "gif-card";
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute(
      "aria-label",
      `View details for ${item.original_filename}`,
    );

    const image = document.createElement("img");
    image.src = mediaPreviewUrl(item.id);
    image.alt = "";
    image.addEventListener("error", () => {
      image.src = item.file_url;
    });

    const filename = document.createElement("p");
    filename.className = "filename";
    filename.textContent = item.original_filename;
    filename.title = item.original_filename;

    card.append(image, filename);
    card.addEventListener("click", () => showDetails(item));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        showDetails(item);
      }
    });
    grid.append(card);
  });
}

async function main() {
  try {
    media = await getMedia();
    populateFilters();
    renderGrid();
    console.log(
      `[gif-finder] browse page loaded ${media.length} media records`,
    );
  } catch (error) {
    console.error("[gif-finder] could not load browse page", error);
    grid.innerHTML = `<div class="empty-state">Could not load media: ${error.message}</div>`;
  }

  Object.values(filters).forEach((filter) =>
    filter.addEventListener("change", renderGrid),
  );

  document.getElementById("clear-filters").addEventListener("click", () => {
    Object.values(filters).forEach((filter) => {
      filter.value = "";
    });
    renderGrid();
  });

  document
    .getElementById("close-dialog")
    .addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
}

main();
