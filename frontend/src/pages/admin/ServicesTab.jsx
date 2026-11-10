import { useEffect, useState } from "react";
import { Loader2, Plus, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { adminApi, fileUrl, formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const EMPTY = { title: "", description: "", price: "", timeline: "", image: "" };

export default function ServicesTab() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await adminApi({ url: "/admin/services" });
      setServices(r.data);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const patch = (id, fields) => {
    setServices((list) => list.map((s) => (s.id === id ? { ...s, ...fields } : s)));
  };

  const saveRow = async (s) => {
    setSavingId(s.id);
    try {
      await adminApi({
        url: `/admin/services/${s.id}`,
        method: "PUT",
        data: { price: s.price, timeline: s.timeline, active: s.active, description: s.description },
      });
      toast.success(`Saved: ${s.title}`);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setSavingId(null);
    }
  };

  const addService = async () => {
    if (form.title.trim().length < 2) {
      toast.error("Please give the service a name.");
      return;
    }
    setSaving(true);
    try {
      await adminApi({ url: "/admin/services", method: "POST", data: form });
      toast.success("Service added.");
      setOpen(false);
      setForm(EMPTY);
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  const removeService = async (s) => {
    try {
      await adminApi({ url: `/admin/services/${s.id}`, method: "DELETE" });
      toast.success("Service removed.");
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    }
  };

  if (loading) {
    return <div className="grid place-items-center py-16"><Loader2 className="w-7 h-7 animate-spin text-brass" /></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="font-serif text-2xl">Services & Prices</h2>
          <p className="text-sm text-espresso-muted mt-0.5">Change a price and press Save — your website updates instantly.</p>
        </div>
        <Button onClick={() => setOpen(true)} className="rounded-full bg-espresso hover:bg-espresso-soft text-cream h-11 px-5" data-testid="admin-add-service-button">
          <Plus className="w-4 h-4 mr-1.5" /> Add Service
        </Button>
      </div>

      <div className="mt-7 space-y-4" data-testid="admin-services-list">
        {services.map((s, i) => (
          <div key={s.id} className="rounded-2xl border border-[#E6DEC8] bg-card p-5" data-testid={`admin-service-row-${i}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3.5 min-w-0">
                {s.image && (
                  <img src={fileUrl(s.image)} alt="" className="w-14 h-14 rounded-xl object-cover shrink-0" />
                )}
                <div className="min-w-0">
                  <h3 className="font-serif text-xl leading-snug truncate">{s.title}</h3>
                  <p className="text-xs text-espresso-muted mt-0.5 line-clamp-1">{s.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <label className="flex items-center gap-2 text-xs font-semibold text-espresso-muted">
                  <Switch checked={s.active} onCheckedChange={(v) => patch(s.id, { active: v })} data-testid={`admin-service-active-${i}`} />
                  Shown
                </label>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-9 w-9 text-terracotta hover:text-terracotta" data-testid={`admin-delete-service-${i}`}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent className="bg-cream border-[#E6DEC8]">
                    <AlertDialogHeader>
                      <AlertDialogTitle className="font-serif">Remove "{s.title}"?</AlertDialogTitle>
                      <AlertDialogDescription>The service disappears from your website. This cannot be undone.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel className="rounded-full">Keep it</AlertDialogCancel>
                      <AlertDialogAction onClick={() => removeService(s)} className="rounded-full bg-terracotta hover:bg-terracotta/90">Remove</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>

            <div className="mt-4 grid sm:grid-cols-[1fr_1fr_auto] gap-3 items-end">
              <div>
                <Label htmlFor={`price-${s.id}`} className="text-xs font-bold text-espresso-muted">PRICE (shown on website)</Label>
                <Input
                  id={`price-${s.id}`}
                  value={s.price}
                  onChange={(e) => patch(s.id, { price: e.target.value })}
                  placeholder="e.g. ₹1,80,000 onwards"
                  className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white font-mono"
                  data-testid={`admin-edit-price-input-${i}`}
                />
              </div>
              <div>
                <Label htmlFor={`timeline-${s.id}`} className="text-xs font-bold text-espresso-muted">TIME TAKEN</Label>
                <Input
                  id={`timeline-${s.id}`}
                  value={s.timeline}
                  onChange={(e) => patch(s.id, { timeline: e.target.value })}
                  placeholder="e.g. 45–90 days"
                  className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white"
                  data-testid={`admin-edit-timeline-input-${i}`}
                />
              </div>
              <Button onClick={() => saveRow(s)} disabled={savingId === s.id} className="h-11 rounded-full bg-espresso hover:bg-espresso-soft text-cream px-5" data-testid={`admin-save-service-${i}`}>
                {savingId === s.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4 mr-1.5" /> Save</>}
              </Button>
            </div>
          </div>
        ))}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="bg-cream border-[#E6DEC8] sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">Add Service</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <Label htmlFor="svc-title" className="text-sm font-bold">Name *</Label>
              <Input id="svc-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Modular Kitchen" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-service-title-input" />
            </div>
            <div>
              <Label htmlFor="svc-desc" className="text-sm font-bold">Description</Label>
              <Textarea id="svc-desc" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="mt-1.5 rounded-xl border-[#E6DEC8] bg-white resize-none" data-testid="admin-service-description-input" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="svc-price" className="text-sm font-bold">Price</Label>
                <Input id="svc-price" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} placeholder="₹… onwards" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-service-price-input" />
              </div>
              <div>
                <Label htmlFor="svc-timeline" className="text-sm font-bold">Time</Label>
                <Input id="svc-timeline" value={form.timeline} onChange={(e) => setForm({ ...form, timeline: e.target.value })} placeholder="e.g. 30 days" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-service-timeline-input" />
              </div>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setOpen(false)} className="rounded-full border-[#E6DEC8]">Cancel</Button>
            <Button onClick={addService} disabled={saving} className="rounded-full bg-espresso hover:bg-espresso-soft text-cream px-6" data-testid="admin-service-save-button">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Add Service"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
