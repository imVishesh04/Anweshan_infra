import { useEffect, useState } from "react";
import { Loader2, Pencil, Plus, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { adminApi, fileUrl, formatApiError } from "@/lib/api";
import { MAX_UPLOAD_MB, compressImage } from "@/lib/compressImage";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

const CATS = [
  { v: "homes", label: "Homes" },
  { v: "shops", label: "Shops" },
  { v: "furniture", label: "Furniture" },
];
const CAT_LABEL = { homes: "Home", shops: "Shop", furniture: "Furniture" };
const EMPTY = { title: "", category: "homes", description: "", image: "" };

export default function IdeasTab() {
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [saving, setSaving] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const setPreviewUrl = (url) => {
    setPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return url;
    });
  };

  const load = async () => {
    setLoading(true);
    try {
      const r = await adminApi({ url: "/admin/ideas" });
      setIdeas(Array.isArray(r.data) ? r.data : []);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openAdd = () => {
    setEditing(null);
    setForm(EMPTY);
    setFile(null);
    setPreviewUrl("");
    setOpen(true);
  };

  const openEdit = (idea) => {
    setEditing(idea);
    // Only web links are shown in the link box; an uploaded photo stays as it is
    // unless a new photo or link is given (an empty box never removes it).
    const isLink = (idea.image || "").startsWith("http");
    setForm({ title: idea.title, category: idea.category, description: idea.description || "", image: isLink ? idea.image : "" });
    setFile(null);
    setPreviewUrl("");
    setOpen(true);
  };

  const onFile = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setPreparing(true);
    try {
      const small = await compressImage(f);
      if (small.size > MAX_UPLOAD_MB * 1024 * 1024) {
        toast.error(`This photo is too big (${(small.size / 1048576).toFixed(1)} MB). Please choose a photo under ${MAX_UPLOAD_MB} MB.`);
        e.target.value = "";
        return;
      }
      setFile(small);
      setPreviewUrl(URL.createObjectURL(small));
    } finally {
      setPreparing(false);
    }
  };

  const save = async () => {
    if (form.title.trim().length < 2) {
      toast.error("Please give the idea a name.");
      return;
    }
    if (!form.image.trim() && !file && !(editing && editing.image)) {
      toast.error("Please add a photo — upload one or paste a link.");
      return;
    }
    setSaving(true);
    try {
      let image = form.image.trim();
      if (file) {
        const fd = new FormData();
        fd.append("file", file);
        const up = await adminApi({ url: "/admin/upload", method: "POST", data: fd });
        image = up.data.path;
      }
      const payload = { title: form.title.trim(), category: form.category, description: form.description.trim() };
      if (image) payload.image = image;
      if (editing) {
        await adminApi({ url: `/admin/ideas/${editing.id}`, method: "PUT", data: payload });
      } else {
        await adminApi({ url: "/admin/ideas", method: "POST", data: payload });
      }
      toast.success(editing ? "Idea updated." : "Idea added — it is live on your website now!");
      setOpen(false);
      setFile(null);
      setPreviewUrl("");
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (idea) => {
    if (deletingId) return;
    setDeletingId(idea.id);
    try {
      await adminApi({ url: `/admin/ideas/${idea.id}`, method: "DELETE" });
      toast.success("Idea deleted.");
      setIdeas((list) => list.filter((i) => i.id !== idea.id));
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="font-serif text-2xl">Design Ideas</h2>
          <p className="text-sm text-espresso-muted mt-0.5">Photos your customers see in the gallery.</p>
        </div>
        <Button onClick={openAdd} className="rounded-full bg-espresso hover:bg-espresso-soft text-cream h-11 px-5" data-testid="admin-add-idea-button">
          <Plus className="w-4 h-4 mr-1.5" /> Add Idea
        </Button>
      </div>

      {loading ? (
        <div className="mt-10 grid place-items-center"><Loader2 className="w-7 h-7 animate-spin text-brass" /></div>
      ) : ideas.length === 0 ? (
        <div className="mt-8 rounded-2xl border border-dashed border-[#E6DEC8] p-10 text-center text-espresso-muted">
          No ideas yet. Click "Add Idea" to add your first design.
        </div>
      ) : (
        <div className="mt-7 grid sm:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="admin-ideas-list">
          {ideas.map((idea) => (
            <div key={idea.id} className="rounded-2xl border border-[#E6DEC8] bg-card overflow-hidden" data-testid={`admin-idea-${idea.id}`}>
              <div className="h-40 bg-cream-alt overflow-hidden">
                {idea.image ? (
                  <img src={fileUrl(idea.image)} alt={idea.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full grid place-items-center text-espresso-muted text-sm">No image</div>
                )}
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-brass-dark">{CAT_LABEL[idea.category]}</span>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-11 w-11" onClick={() => openEdit(idea)} aria-label="Edit idea" data-testid={`admin-edit-idea-${idea.id}`}>
                      <Pencil className="w-4 h-4" />
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" size="icon" disabled={deletingId === idea.id} className="h-11 w-11 text-terracotta hover:text-terracotta" aria-label="Delete idea" data-testid={`admin-delete-idea-${idea.id}`}>
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent className="bg-cream border-[#E6DEC8]">
                        <AlertDialogHeader>
                          <AlertDialogTitle className="font-serif">Delete "{idea.title}"?</AlertDialogTitle>
                          <AlertDialogDescription>This removes the design idea from your website. This cannot be undone.</AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel className="rounded-full">Keep it</AlertDialogCancel>
                          <AlertDialogAction onClick={() => remove(idea)} className="rounded-full bg-terracotta hover:bg-terracotta/90">Delete</AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
                <h3 className="mt-1.5 font-serif text-lg leading-snug">{idea.title}</h3>
                {idea.description && <p className="mt-1 text-xs text-espresso-muted line-clamp-2">{idea.description}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="bg-cream border-[#E6DEC8] max-h-[90vh] overflow-y-auto sm:max-w-lg" data-testid="admin-idea-dialog">
          <DialogHeader>
            <DialogTitle className="font-serif text-2xl">{editing ? "Edit Design Idea" : "Add Design Idea"}</DialogTitle>
          </DialogHeader>

          <div className="space-y-5 mt-2">
            <div>
              <Label htmlFor="idea-title" className="text-sm font-bold">Name of the design *</Label>
              <Input id="idea-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Warm Cream Living Room" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-idea-title-input" />
            </div>

            <div>
              <Label className="text-sm font-bold">Where does it belong? *</Label>
              <div className="grid grid-cols-3 gap-2 mt-1.5">
                {CATS.map((c) => (
                  <button
                    key={c.v}
                    type="button"
                    aria-pressed={form.category === c.v}
                    onClick={() => setForm({ ...form, category: c.v })}
                    className={`h-10 rounded-full text-sm font-bold transition-colors ${form.category === c.v ? "bg-espresso text-cream" : "border border-[#E6DEC8] bg-white text-espresso hover:border-brass"}`}
                    data-testid={`admin-idea-category-${c.v}`}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <Label htmlFor="idea-photo" className="flex items-center gap-2 text-sm font-bold">
                <Upload className="w-4 h-4 text-brass-dark" /> Upload photo (from your phone/computer)
              </Label>
              <Input id="idea-photo" type="file" accept="image/*" onChange={onFile} className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-idea-photo-input" />
            </div>

            {preparing && (
              <p className="text-sm text-espresso-muted flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Preparing photo…</p>
            )}
            {(preview || form.image || editing?.image) && (
              <div className="h-36 rounded-xl overflow-hidden border border-[#E6DEC8] bg-white">
                <img src={preview || fileUrl(form.image || editing?.image)} alt="preview" className="w-full h-full object-cover" />
              </div>
            )}
            {editing?.image && !preview && !form.image && (
              <p className="text-xs text-espresso-muted -mt-3">The current photo stays unless you upload a new one.</p>
            )}

            <div>
              <Label htmlFor="idea-url" className="text-sm font-bold">…or paste a photo link</Label>
              <Input id="idea-url" value={form.image} onChange={(e) => setForm({ ...form, image: e.target.value })} placeholder="https://… (optional)" className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-idea-url-input" />
            </div>

            <div>
              <Label htmlFor="idea-desc" className="text-sm font-bold">Short description</Label>
              <Textarea id="idea-desc" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} placeholder="One or two lines about this design…" className="mt-1.5 rounded-xl border-[#E6DEC8] bg-white resize-none" data-testid="admin-idea-description-input" />
            </div>
          </div>

          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setOpen(false)} className="rounded-full border-[#E6DEC8]" data-testid="admin-idea-cancel-button">Cancel</Button>
            <Button onClick={save} disabled={saving || preparing} className="rounded-full bg-espresso hover:bg-espresso-soft text-cream px-6" data-testid="admin-idea-save-button">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : editing ? "Save Changes" : "Add to Website"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
