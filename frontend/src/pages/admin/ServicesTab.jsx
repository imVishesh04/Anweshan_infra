import { useEffect, useState } from "react";
import { ImagePlus, Loader2, Plus, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { adminApi, fileUrl, formatApiError } from "@/lib/api";
import { MAX_UPLOAD_MB, compressImage } from "@/lib/compressImage";
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
  const [dirty, setDirty] = useState({});
  const [photoId, setPhotoId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await adminApi({ url: "/admin/services" });
      setServices(Array.isArray(r.data) ? r.data : []);
      setDirty({});
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const patch = (id, fields, markDirty = true) => {
    setServices((list) => list.map((s) => (s.id === id ? { ...s, ...fields } : s)));
    if (markDirty) setDirty((d) => ({ ...d, [id]: true }));
  };

  // The "Shown" switch saves straight away, so a hidden service is really hidden.
  const toggleActive = async (s, value) => {
    patch(s.id, { active: value }, false);
    try {
      await adminApi({ url: `/admin/services/${s.id}`, method: "PUT", data: { active: value } });
      toast.success(value ? `"${s.title}" is shown on the website.` : `"${s.title}" is hidden from the website.`);
    } catch (e) {
      patch(s.id, { active: !value }, false);
      toast.error(formatApiError(e));
    }
  };

  const changePhoto = async (s, e) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    setPhotoId(s.id);
    try {
      const small = await compressImage(f);
      if (small.size > MAX_UPLOAD_MB * 1024 * 1024) {
        toast.error(`This photo is too big. Please choose a photo under ${MAX_UPLOAD_MB} MB.`);
        return;
      }
      const fd = new FormData();
      fd.append("file", small);
      const up = await adminApi({ url: "/admin/upload", method: "POST", data: fd });
      await adminApi({ url: `/admin/services/${s.id}`, method: "PUT", data: { image: up.data.path } });
      patch(s.id, { image: up.data.path }, false);
      toast.success("Photo updated.");
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setPhotoId(null);
    }
  };

  const saveRow = async (s) => {
    if ((s.title || "").trim().length < 2) {
      toast.error("Please give the service a name.");
      return;
    }
    setSavingId(s.id);
    try {
      await adminApi({
        url: `/admin/services/${s.id}`,
        method: "PUT",
        data: { title: s.title.trim(), price: s.price, timeline: s.timeline, description: s.description },
      });
      setDirty((d) => ({ ...d, [s.id]: false }));
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
      const r = await adminApi({ url: "/admin/services", method: "POST", data: form });
      toast.success("Service added.");
      setOpen(false);
      setForm(EMPTY);
      // Add it to the list without reloading, so unsaved edits in other rows stay.
      setServices((list) => [...list, r.data]);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  const removeService = async (s) => {
    if (deletingId) return;
    setDeletingId(s.id);
    try {
      await adminApi({ url: `/admin/services/${s.id}`, method: "DELETE" });
      toast.success("Service removed.");
      setServices((list) => list.filter((x) => x.id !== s.id));
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setDeletingId(null);
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
              <div className="flex items-start gap-3.5 min-w-0 flex-1">
                <label className="relative shrink-0 w-16 h-16 rounded-xl overflow-hidden border border-[#E6DEC8] bg-cream-alt cursor-pointer grid place-items-center" title="Change photo">
                  {s.image ? (
                    <img src={fileUrl(s.image)} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <ImagePlus className="w-5 h-5 text-espresso-muted" />
                  )}
                  {photoId === s.id && (
                    <span className="absolute inset-0 grid place-items-center bg-cream/80"><Loader2 className="w-5 h-5 animate-spin text-brass" /></span>
                  )}
                  <input type="file" accept="image/*" className="sr-only" aria-label={`Change photo for ${s.title}`} onChange={(e) => changePhoto(s, e)} />
                </label>
                <div className="min-w-0 flex-1 space-y-1.5">
                  <Input
                    value={s.title}
                    onChange={(e) => patch(s.id, { title: e.target.value })}
                    aria-label="Service name"
                    className="h-10 rounded-xl border-[#E6DEC8] bg-white font-serif text-lg"
                  />
                  <Textarea
                    value={s.description}
                    onChange={(e) => patch(s.id, { description: e.target.value })}
                    aria-label="Service description"
                    rows={2}
                    className="rounded-xl border-[#E6DEC8] bg-white text-sm resize-none"
                  />
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <label className="flex items-center gap-2 text-xs font-semibold text-espresso-muted">
                  <Switch checked={s.active} onCheckedChange={(v) => toggleActive(s, v)} data-testid={`admin-service-active-${i}`} />
                  Shown
                </label>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="ghost" size="icon" disabled={deletingId === s.id} aria-label={`Delete ${s.title}`} className="h-11 w-11 text-terracotta hover:text-terracotta" data-testid={`admin-delete-service-${i}`}>
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
              <Button
                onClick={() => saveRow(s)}
                disabled={savingId === s.id}
                className={`h-11 rounded-full text-cream px-5 ${dirty[s.id] ? "bg-terracotta hover:bg-terracotta/90" : "bg-espresso hover:bg-espresso-soft"}`}
                data-testid={`admin-save-service-${i}`}
              >
                {savingId === s.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4 mr-1.5" /> {dirty[s.id] ? "Save changes" : "Save"}</>}
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
