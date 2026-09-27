// Static files are served by FastAPI at /app, so API requests use same-origin paths.
const API_BASE_URL =
  window.location.protocol === "file:" ? "http://127.0.0.1:8001" : "";

async function request(path, options) {
  console.log(`[gif-finder] ${options?.method || "GET"} ${path}`);
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  console.log(`Fetching media from ${API_BASE_URL}${path}`);
  console.log(`[gif-finder] Response status: ${response.status}`);
  if (response.ok) return response.json();
  let detail = `Request failed (${response.status})`;

  try {
    detail = (await response.json()).detail || detail;
  } catch {
    /* A non-JSON error is still useful. */
  }

  throw new Error(detail);
}

export const getMedia = () => request("/media");
export const getTags = () => request("/tags");
export const getStreams = () => request("/streams");
export const sendMedia = (mediaData) =>
  request("/media", { method: "POST", body: mediaData });
export const mediaPreviewUrl = (mediaId) =>
  `${API_BASE_URL}/media/${mediaId}/preview`;
