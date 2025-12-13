// frontend/src/utils/api.ts
import axios from "axios";

/*
 * Backend base URL
 * - Local dev: http://localhost:5000
 * - Production (Vercel): use env variable
 */
const BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:5000";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 20000,
});

/* -------------------- API FUNCTIONS -------------------- */

export async function getTechnologies() {
  const res = await client.get("/api/technologies");
  return res.data;
}

export async function getSentiment(
  technology: string,
  refresh = false
) {
  const params = refresh ? { refresh: "true" } : undefined;
  const res = await client.get(
    `/api/sentiment/${encodeURIComponent(technology)}`,
    { params }
  );
  return res.data;
}

export async function getInsights(technology: string) {
  const res = await client.get(
    `/api/insights/${encodeURIComponent(technology)}`
  );
  return res.data;
}

export async function postCompare(technologies: string[]) {
  const res = await client.post("/api/compare", { technologies });
  return res.data;
}

export async function postAnalyze(text: string) {
  const res = await client.post("/api/analyze", { text });
  return res.data;
}

export async function getStats() {
  const res = await client.get("/api/stats");
  return res.data;
}

/**
 * Optional endpoint — backend may not expose this.
 * Do NOT fail frontend if missing.
 */
export async function getModelInfo() {
  try {
    const res = await client.get("/api/model-info");
    return res.data;
  } catch {
    return null;
  }
}

export default client;
