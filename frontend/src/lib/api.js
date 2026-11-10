import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  withCredentials: true,
  timeout: 30000,
});

// Admin calls: on 401, silently refresh the session once and retry.
export async function adminApi(config) {
  try {
    return await api(config);
  } catch (e) {
    if (e?.response?.status === 401) {
      await api.post("/admin/refresh");
      return await api(config);
    }
    throw e;
  }
}

export function formatApiError(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (detail == null) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(", ") || fallback;
  }
  if (detail && typeof detail.msg === "string") return detail.msg;
  return fallback;
}

export function fileUrl(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API}/files/${path}`;
}

export const digits = (s) => (s || "").replace(/\D/g, "");

export function waLink(number, text) {
  return `https://wa.me/${digits(number)}?text=${encodeURIComponent(text)}`;
}

export function scrollToId(id) {
  const el = document.getElementById(id);
  if (!el) return;
  if (window.__lenis) {
    window.__lenis.scrollTo(el, { offset: -64, duration: 1.2 });
  } else {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

export function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  } catch (e) {
    return iso || "";
  }
}
