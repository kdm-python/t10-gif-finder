const BACKEND_URL = "http://127.0.0.1:8001";

export async function getMedia() {
  const response = await fetch(`${BACKEND_URL}/media`);

  if (!response.ok) {
    throw new Error("Failed to load media");
  }

  const media = await response.json();

  // Sort by date key

  return media;
}

export async function sendMedia(mediaData) {
  const response = await fetch(`${BACKEND_URL}/media`, {
    method: "POST",
    body: mediaData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload media");
  }

  return response.json();
}

export async function getTags() {
  const response = await fetch(`${BACKEND_URL}/tags`);

  if (!response.ok) {
    throw new Error("Failed to load tags");
  }

  return response.json();
}

export async function getStreams() {
  const response = await fetch(`${BACKEND_URL}/streams`);

  if (!response.ok) {
    throw new Error("Failed to load streams");
  }

  return response.json();
}
