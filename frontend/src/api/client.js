import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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

export const getEDA = async (datasetId, aiInsights = true) => {
  const { data } = await client.get(`/api/dataset/${datasetId}/eda`, {
    params: { ai_insights: aiInsights },
  });
  return data;
};

export const getExecutiveSummary = async (datasetId) => {
  const { data } = await client.get(`/api/dataset/${datasetId}/executive-summary`);
  return data;
};

export const indexDatasetForChat = async (datasetId) => {
  const { data } = await client.post(`/api/dataset/${datasetId}/index`);
  return data;
};

export const getIndexStatus = async (datasetId) => {
  const { data } = await client.get(`/api/dataset/${datasetId}/index-status`);
  return data;
};

export const askQuestion = async (datasetId, question, topK = 6) => {
  const { data } = await client.post(`/api/dataset/chat`, {
    dataset_id: datasetId,
    question,
    top_k: topK,
  });
  return data;
};

export default client;
