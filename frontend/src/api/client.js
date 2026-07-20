import axios from "axios";

// On Vercel, the frontend and backend share the same origin (e.g. myapp.vercel.app).
// Using an empty string means all /api/* calls are same-origin — no CORS needed.
// Override via VITE_API_BASE_URL env var if deploying frontend and backend separately.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://dataset-explorer-three.vercel.app";

const client = axios.create({ baseURL: API_BASE_URL });

export const uploadDataset = async (file) => {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post("/api/dataset/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const getCleaningReport = async (datasetId) => {
  const { data } = await client.get(`/api/dataset/${datasetId}/cleaning-report`);
  return data;
};

export const getEDA = async (datasetId, aiInsights = true, onProgress = null) => {
  const url = `${API_BASE_URL}/api/dataset/${datasetId}/eda?ai_insights=${aiInsights}`;

  const response = await fetch(url, {
    headers: { Accept: "text/event-stream" },
  });
  if (!response.ok) {
    let errorDetail = `HTTP error! status: ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch (e) {}
    throw new Error(errorDetail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (value) {
      buffer += decoder.decode(value, { stream: true });
    }

    // Process every complete line in the buffer
    let newlineIdx;
    while ((newlineIdx = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, newlineIdx).trim();
      buffer = buffer.slice(newlineIdx + 1);

      if (!line.startsWith("data: ")) continue;

      const raw = line.slice(6).trim();
      if (!raw || raw === "[DONE]") continue;

      let parsed;
      try {
        parsed = JSON.parse(raw);
      } catch (e) {
        console.warn("SSE JSON parse failed, skipping line:", raw.slice(0, 120), e.message);
        continue;
      }

      if (parsed.type === "error") {
        throw new Error(parsed.error || "Unknown server error");
      }
      if (parsed.type === "progress") {
        if (onProgress) onProgress(parsed.message);
        continue;
      }
      if (parsed.type === "complete") {
        reader.cancel(); // release the stream
        return parsed.data;
      }
    }

    if (done) break;
  }

  throw new Error("Stream closed before a 'complete' event was received.");
};

export const getExecutiveSummary = async (datasetId) => {
  const { data } = await client.get(`/api/dataset/${datasetId}/executive-summary`);
  return data;
};

export default client;
