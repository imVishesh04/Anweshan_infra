import { useEffect, useState } from "react";
import { KeyRound, Loader2, RefreshCw, Save } from "lucide-react";
import { toast } from "sonner";
import { adminApi, api, formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const EMPTY = { phone: "", whatsapp: "", instagram: "", address: "", hours: "" };

function ChangePassword() {
  const [pw, setPw] = useState({ current: "", next: "", again: "" });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    if (pw.next.length < 8) return toast.error("New password must be at least 8 characters.");
    if (pw.next !== pw.again) return toast.error("The two new passwords do not match.");
    setBusy(true);
    try {
      await adminApi({
        url: "/admin/password",
        method: "PUT",
        data: { current_password: pw.current, new_password: pw.next },
      });
      setPw({ current: "", next: "", again: "" });
      toast.success("Password changed. Other phones/computers are logged out.");
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  const field = (key, id, label) => (
    <div>
      <Label htmlFor={id} className="text-sm font-bold">{label}</Label>
      <Input
        id={id}
        type="password"
        autoComplete={key === "current" ? "current-password" : "new-password"}
        value={pw[key]}
        onChange={(e) => setPw({ ...pw, [key]: e.target.value })}
        className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white"
      />
    </div>
  );

  return (
    <div className="mt-12 rounded-2xl border border-[#E6DEC8] bg-card p-5 sm:p-6">
      <h3 className="font-serif text-xl flex items-center gap-2"><KeyRound className="w-5 h-5 text-brass-dark" /> Change admin password</h3>
      <div className="mt-5 space-y-4">
        {field("current", "pw-current", "Current password")}
        {field("next", "pw-next", "New password (at least 8 characters)")}
        {field("again", "pw-again", "New password again")}
        <Button onClick={save} disabled={busy || !pw.current || !pw.next} className="rounded-full bg-espresso hover:bg-espresso-soft text-cream h-11 px-6">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : "Change Password"}
        </Button>
      </div>
    </div>
  );
}

export default function SettingsTab() {
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const [loadFailed, setLoadFailed] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    setLoadFailed(false);
    api
      .get("/site")
      .then((r) => {
        const d = r.data || {};
        setForm({ phone: d.phone || "", whatsapp: d.whatsapp || "", instagram: d.instagram || "", address: d.address || "", hours: d.hours || "" });
      })
      .catch(() => setLoadFailed(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const save = async () => {
    if (!form.phone.trim() || !form.whatsapp.trim()) {
      toast.error("Phone and WhatsApp numbers cannot be empty.");
      return;
    }
    setSaving(true);
    try {
      const r = await adminApi({ url: "/admin/settings", method: "PUT", data: form });
      const d = r.data || {};
      // Show the cleaned-up numbers the server saved (e.g. "+91 98765 43210").
      setForm({ phone: d.phone || "", whatsapp: d.whatsapp || "", instagram: d.instagram || "", address: d.address || "", hours: d.hours || "" });
      toast.success("Saved! Your website contact buttons now use these details.");
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="grid place-items-center py-16"><Loader2 className="w-7 h-7 animate-spin text-brass" /></div>;
  }

  if (loadFailed) {
    // Never show an empty form that could be saved over the real details.
    return (
      <div className="max-w-xl rounded-2xl border border-dashed border-[#E6DEC8] p-8 text-center">
        <p className="text-espresso-muted">Could not load your contact info. Please check your internet.</p>
        <Button onClick={load} variant="outline" className="mt-4 rounded-full border-[#E6DEC8]">
          <RefreshCw className="w-4 h-4 mr-2" /> Try again
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-xl">
      <h2 className="font-serif text-2xl">My Contact Info</h2>
      <p className="text-sm text-espresso-muted mt-0.5">These appear on every WhatsApp, Call and Instagram button on your website.</p>

      <div className="mt-7 space-y-5">
        <div>
          <Label htmlFor="set-phone" className="text-sm font-bold">Phone number (for Call buttons)</Label>
          <Input id="set-phone" type="tel" inputMode="tel" value={form.phone} onChange={set("phone")} placeholder="e.g. 98765 43210" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-settings-phone-input" />
        </div>
        <div>
          <Label htmlFor="set-wa" className="text-sm font-bold">WhatsApp number</Label>
          <Input id="set-wa" type="tel" inputMode="tel" value={form.whatsapp} onChange={set("whatsapp")} placeholder="e.g. 98765 43210" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-settings-whatsapp-input" />
          <p className="mt-1 text-xs text-espresso-muted">A 10-digit Indian number is fine — we add +91 for you.</p>
        </div>
        <div>
          <Label htmlFor="set-insta" className="text-sm font-bold">Instagram link or @username</Label>
          <Input id="set-insta" value={form.instagram} onChange={set("instagram")} placeholder="@anweshaninfra" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-settings-instagram-input" />
        </div>
        <div>
          <Label htmlFor="set-address" className="text-sm font-bold">Studio address (optional)</Label>
          <Input id="set-address" value={form.address} onChange={set("address")} placeholder="Shop 12, Main Road, Your City" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-settings-address-input" />
        </div>
        <div>
          <Label htmlFor="set-hours" className="text-sm font-bold">Working hours (optional)</Label>
          <Input id="set-hours" value={form.hours} onChange={set("hours")} placeholder="e.g. Mon–Sat, 10 AM – 7 PM" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-settings-hours-input" />
        </div>

        <Button onClick={save} disabled={saving} className="rounded-full bg-espresso hover:bg-espresso-soft text-cream h-12 px-7" data-testid="admin-settings-save-button">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4 mr-2" /> Save Contact Info</>}
        </Button>
      </div>

      <ChangePassword />
    </div>
  );
}
