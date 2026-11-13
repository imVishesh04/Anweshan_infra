import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  withCredentials: true,
  // Netlify's proxy gives up after 26 s, so wait a little less than that.
  timeout: 20000,
});

export const SESSION_EXPIRED_EVENT = "admin-session-expired";

// Admin calls: on 401, refresh the session once (shared by all calls that fail
// at the same moment) and retry. If the refresh itself fails, tell the admin
// page so it can show the login screen instead of a dashboard full of errors.
let refreshPromise = null;
export async function adminApi(config) {
  try {
    return await api(config);
  } catch (e) {
    if (e?.response?.status !== 401) throw e;
    try {
      if (!refreshPromise) {
        refreshPromise = api.post("/admin/refresh").finally(() => {
          refreshPromise = null;
        });
      }
      await refreshPromise;
    } catch (refreshErr) {
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
      throw refreshErr;
    }
    return await api(config);
  }
}

export function formatApiError(error, fallback = "Something went wrong. Please try again.") {
  if (error && !error.response) {
    if (error.code === "ECONNABORTED") return "It took too long. Please check your internet and try again.";
    return "Can't reach the server. Please check your internet and try again.";
  }
  const status = error?.response?.status;
  const detail = error?.response?.data?.detail;
  if (status === 502 || status === 503 || status === 504) {
    return "The server is busy or waking up. Please try again in a minute.";
  }
  if (status === 413) return typeof detail === "string" ? detail : "The file is too big.";
  if (detail == null) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return (
      detail
        .map((e) => {
          if (!e || typeof e.msg !== "string") return "";
          const field = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : "";
          return field && field !== "body" ? `${field}: ${e.msg}` : e.msg;
        })
        .filter(Boolean)
        .join(", ") || fallback
    );
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

// WhatsApp and phone links need the full international number.
// "98765 43210", "098765-43210" and "+91 98765 43210" all become "919876543210".
export function intlDigits(number) {
  let d = digits(number);
  if (d.startsWith("00")) d = d.slice(2);
  if (d.length === 11 && d.startsWith("0")) d = d.slice(1);
  if (d.length === 10) d = `91${d}`;
  return d;
}

export function waLink(number, text) {
  const d = intlDigits(number);
  if (!d) return "#contact";
  return `https://wa.me/${d}?text=${encodeURIComponent(text)}`;
}

// Website WhatsApp buttons add a short code like "Ref: AI-KITCHEN" to the pre-typed
// message, so the WhatsApp bot already knows the service and skips that question.
export function serviceRef(text = "") {
  const t = String(text).toLowerCase();
  if (/kitchen|wardrobe|modular/.test(t)) return "AI-KITCHEN";
  if (/furniture|repair|polish|sofa|chair|assessment|carpent/.test(t)) return "AI-FURNITURE";
  if (/shop|retail|office|caf|restaurant|commercial|store|showroom|salon|boutique|bakery/.test(t)) return "AI-SHOP";
  if (/home|house|flat|apartment|villa|bhk|interior|living|bedroom|nook|lounge/.test(t)) return "AI-HOME";
  return "AI-OTHER";
}

const CATEGORY_REF = { homes: "AI-HOME", shops: "AI-SHOP", furniture: "AI-FURNITURE" };

export function categoryRef(category, title = "") {
  return CATEGORY_REF[category] || serviceRef(title);
}

export function withRef(text, ref) {
  return ref ? `${text}\n\nRef: ${ref}` : text;
}

export function telHref(number) {
  const d = intlDigits(number);
  return d ? `tel:+${d}` : "#contact";
}

// Accept "@handle", "handle" or a full link, and always return a safe https link.
export function instagramUrl(value) {
  const v = (value || "").trim();
  if (!v) return "";
  if (/^https?:\/\//i.test(v)) return v.replace(/^http:/i, "https:");
  if (/instagram\.com\//i.test(v)) return `https://${v.replace(/^\/+/, "")}`;
  return `https://www.instagram.com/${v.replace(/^@/, "")}`;
}

export function scrollToId(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Unsplash sends the full-size original (often several MB) unless a width is asked for.
export function imgUrl(src, width) {
  const url = fileUrl(src);
  if (!url.includes("images.unsplash.com") || /[?&]w=/.test(url)) return url;
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}w=${width}&auto=format&fit=crop`;
}

export function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Kolkata",
    });
  } catch (e) {
    return iso || "";
  }
}
