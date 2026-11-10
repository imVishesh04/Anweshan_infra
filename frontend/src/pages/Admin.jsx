import { useEffect, useState } from "react";
import { ArrowLeft, Loader2, Lock, LogOut } from "lucide-react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { ArchMark } from "@/components/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import IdeasTab from "./admin/IdeasTab";
import ServicesTab from "./admin/ServicesTab";
import EnquiriesTab from "./admin/EnquiriesTab";
import SettingsTab from "./admin/SettingsTab";

export default function Admin() {
  const [authed, setAuthed] = useState(null);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/admin/me")
      .then(() => setAuthed(true))
      .catch(() => setAuthed(false));
  }, []);

  const login = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/admin/login", { password });
      setAuthed(true);
    } catch (err) {
      setError(formatApiError(err, "Wrong password. Please try again."));
    } finally {
      setBusy(false);
    }
  };

  const logout = async () => {
    try {
      await api.post("/admin/logout");
    } catch (e) { /* ignore */ }
    setAuthed(false);
    setPassword("");
  };

  if (authed === null) {
    return (
      <div className="min-h-screen grid place-items-center bg-espresso">
        <Loader2 className="w-8 h-8 animate-spin text-brass" />
      </div>
    );
  }

  if (!authed) {
    return (
      <div className="min-h-screen grid place-items-center bg-espresso grain px-5">
        <form onSubmit={login} className="relative z-10 w-full max-w-sm rounded-[28px] bg-cream p-8 shadow-card text-espresso" data-testid="admin-login-card">
          <div className="flex flex-col items-center text-center">
            <span className="grid place-items-center w-16 h-16 rounded-2xl bg-cream border border-[#E6DEC8] overflow-hidden">
              <ArchMark className="w-12 h-12" />
            </span>
            <h1 className="mt-5 font-serif text-3xl">Studio Admin</h1>
            <p className="mt-1.5 text-sm text-espresso-muted">ANWESHAN Infra · Only for the owner.</p>
          </div>

          <div className="mt-7">
            <label htmlFor="admin-password" className="text-sm font-bold">Password</label>
            <div className="relative mt-2">
              <Lock className="w-4 h-4 text-espresso-muted absolute left-4 top-1/2 -translate-y-1/2" />
              <Input
                id="admin-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="h-12 pl-10 rounded-xl border-[#E6DEC8] bg-white focus-visible:ring-brass/40"
                data-testid="admin-password-input"
              />
            </div>
            {error && (
              <p className="mt-2.5 text-sm font-semibold text-terracotta" data-testid="admin-login-error">{error}</p>
            )}
          </div>

          <Button
            type="submit"
            disabled={busy || !password}
            className="mt-5 w-full h-12 rounded-full bg-espresso hover:bg-espresso-soft text-cream font-bold"
            data-testid="admin-login-button"
          >
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : "Open Studio"}
          </Button>

          <Link to="/" className="mt-5 flex items-center justify-center gap-1.5 text-sm text-espresso-muted hover:text-espresso transition-colors" data-testid="admin-back-to-site">
            <ArrowLeft className="w-4 h-4" /> Back to website
          </Link>
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream text-espresso" data-testid="admin-dashboard">
      <header className="sticky top-0 z-40 bg-cream/85 backdrop-blur-xl border-b border-[#E6DEC8]">
        <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="grid place-items-center w-10 h-10 rounded-xl bg-cream border border-[#E6DEC8] overflow-hidden">
              <ArchMark className="w-7 h-7" />
            </span>
            <span className="font-serif font-semibold tracking-wide text-lg">Studio Admin</span>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/" className="inline-flex items-center gap-1.5 text-sm font-semibold text-espresso-muted hover:text-espresso px-3 h-10 rounded-full hover:bg-cream-alt transition-colors" data-testid="admin-view-site-link">
              <ArrowLeft className="w-4 h-4" /> View Site
            </Link>
            <Button variant="outline" onClick={logout} className="rounded-full border-[#E6DEC8] hover:bg-terracotta hover:text-white" data-testid="admin-logout-button">
              <LogOut className="w-4 h-4 mr-1.5" /> Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 py-8 pb-20">
        <Tabs defaultValue="ideas">
          <TabsList className="bg-cream-alt rounded-full p-1 h-12" data-testid="admin-tabs">
            <TabsTrigger value="ideas" className="rounded-full px-5 data-[state=active]:bg-espresso data-[state=active]:text-cream" data-testid="admin-tab-ideas">Design Ideas</TabsTrigger>
            <TabsTrigger value="services" className="rounded-full px-5 data-[state=active]:bg-espresso data-[state=active]:text-cream" data-testid="admin-tab-services">Services & Prices</TabsTrigger>
            <TabsTrigger value="enquiries" className="rounded-full px-5 data-[state=active]:bg-espresso data-[state=active]:text-cream" data-testid="admin-tab-enquiries">Enquiries</TabsTrigger>
            <TabsTrigger value="settings" className="rounded-full px-5 data-[state=active]:bg-espresso data-[state=active]:text-cream" data-testid="admin-tab-settings">My Contact Info</TabsTrigger>
          </TabsList>

          <TabsContent value="ideas" className="mt-8"><IdeasTab /></TabsContent>
          <TabsContent value="services" className="mt-8"><ServicesTab /></TabsContent>
          <TabsContent value="enquiries" className="mt-8"><EnquiriesTab /></TabsContent>
          <TabsContent value="settings" className="mt-8"><SettingsTab /></TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
