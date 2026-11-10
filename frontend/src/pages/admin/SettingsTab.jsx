import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { toast } from "sonner";
import { adminApi, api, formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SettingsTab() {
  const [form, setForm] = useState({ phone: "", whatsapp: "", instagram: "", address: "", hours: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get("/site")
      .then((r) => setForm({ phone: r.data.phone || "", whatsapp: r.data.whatsapp || "", instagram: r.data.instagram || "", address: r.data.address || "", hours: r.data.hours || "" }))
      .catch(() => toast.error("Could not load settings."))
      .finally(() => setLoading(false));
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const save = async () => {
    setSaving(true);
    try {
      await adminApi({ url: "/admin/settings", method: "PUT", data: form });
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

  return (
    <div className="max-w-xl">
      <h2 className="font-serif text-2xl">My Contact Info</h2>
      <p className="text-sm text-espresso-muted mt-0.5">These appear on every WhatsApp, Call and Instagram button on your website.</p>

      <div className="mt-7 space-y-5">
        <div>
          <Label htmlFor="set-phone" className="text-sm font-bold">Phone number (for Call buttons)</Label>
          <Input id="set-phone" value={form.phone} onChange={set("phone")} placeholder="e.g. +91 98765 43210" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-settings-phone-input" />
        </div>
        <div>
          <Label htmlFor="set-wa" className="text-sm font-bold">WhatsApp number (with country code)</Label>
          <Input id="set-wa" value={form.whatsapp} onChange={set("whatsapp")} placeholder="e.g. 91 98765 43210" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-settings-whatsapp-input" />
        </div>
        <div>
          <Label htmlFor="set-insta" className="text-sm font-bold">Instagram link</Label>
          <Input id="set-insta" value={form.instagram} onChange={set("instagram")} placeholder="https://instagram.com/yourname" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-settings-instagram-input" />
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
    </div>
  );
}
