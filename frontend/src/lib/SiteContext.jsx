import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "./api";

const SiteContext = createContext(null);

export const useSite = () => useContext(SiteContext);

export function SiteProvider({ children }) {
  const [site, setSite] = useState({ phone: "", whatsapp: "", instagram: "", address: "", hours: "" });
  const [services, setServices] = useState([]);
  const [ready, setReady] = useState(false);

  const reload = useCallback(async () => {
    try {
      const [s, sv] = await Promise.all([api.get("/site"), api.get("/services")]);
      setSite(s.data);
      setServices(sv.data);
    } catch (e) {
      console.error("site load failed", e);
    } finally {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return (
    <SiteContext.Provider value={{ site, services, ready, reload }}>
      {children}
    </SiteContext.Provider>
  );
}
