import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "./api";

const SiteContext = createContext(null);

export const useSite = () => useContext(SiteContext);

// Shown until the server answers (and if it never does), so the WhatsApp and
// Call buttons always work, even on a slow phone or while the server wakes up.
export const DEFAULT_SITE = {
  phone: "+91 86584 29239",
  whatsapp: "+91 86584 29239",
  instagram: "https://www.instagram.com/anweshaninfra",
  address: "",
  hours: "",
};

const keepFilled = (base, incoming) => {
  const out = { ...base };
  Object.entries(incoming || {}).forEach(([k, v]) => {
    if (typeof v === "string" ? v.trim() : v != null) out[k] = v;
  });
  return out;
};

export function SiteProvider({ children }) {
  const [site, setSite] = useState(DEFAULT_SITE);
  const [services, setServices] = useState([]);
  const [ready, setReady] = useState(false);
  const [servicesFailed, setServicesFailed] = useState(false);

  const reload = useCallback(async (attempt = 0) => {
    const [s, sv] = await Promise.allSettled([api.get("/site"), api.get("/services")]);
    if (s.status === "fulfilled" && s.value?.data && typeof s.value.data === "object") {
      setSite((cur) => keepFilled(cur, s.value.data));
    }
    if (sv.status === "fulfilled" && Array.isArray(sv.value?.data)) {
      setServices(sv.value.data);
      setServicesFailed(false);
    } else {
      setServicesFailed(true);
    }
    const anyFailed = s.status === "rejected" || sv.status === "rejected";
    if (anyFailed && attempt === 0) {
      // The server may be waking up; try once more after a short pause.
      setTimeout(() => reload(1), 3000);
      return;
    }
    setReady(true);
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return (
    <SiteContext.Provider value={{ site, services, ready, servicesFailed, reload }}>
      {children}
    </SiteContext.Provider>
  );
}
