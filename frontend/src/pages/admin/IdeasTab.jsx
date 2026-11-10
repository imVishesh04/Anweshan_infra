import { useEffect, useState } from "react";
import { Loader2, Pencil, Plus, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { adminApi, fileUrl, formatApiError } from "@/lib/api";
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

  const load = async () => {
    setLoading(true);
    try {
      const r = await adminApi({ url: "/admin/ideas" });
      setIdeas(r.data);
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
    setPreview("");
    setOpen(true);
  };

  const openEdit = (idea) => {
    setEditing(idea);
    setForm({ title: idea.title, category: idea.category, description: idea.description || "", image: idea.image || "" });
    setFile(null);
    setPreview("");
    setOpen(true);
  };

  const onFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
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
      const payload = { title: form.title.trim(), category: form.category, description: form.description.trim(), image };
      if (editing) {
        await adminApi({ url: `/admin/ideas/${editing.id}`, method: "PUT", data: payload });
      } else {
        await adminApi({ url: "/admin/ideas", method: "POST", data: payload });
      }
      toast.success(editing ? "Idea updated." : "Idea added — it is live on your website now!");
      setOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (idea) => {
    try {
      await adminApi({ url: `/admin/ideas/${idea.id}`, method: "DELETE" });
      toast.success("Idea deleted.");
      load();
    } catch (e) {
      toast.error(formatApiError(e));
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
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(idea)} aria-label="Edit idea" data-testid={`admin-edit-idea-${idea.id}`}>
                      <Pencil className="w-4 h-4" />
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-terracotta hover:text-terracotta" aria-label="Delete idea" data-testid={`admin-delete-idea-${idea.id}`}>
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
              <Input id="idea-photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={onFile} className="mt-1.5 h-11 rounded-xl border-[#E6DEC8] bg-white" data-testid="admin-idea-photo-input" />
            </div>

            {(preview || form.image) && (
              <div className="h-36 rounded-xl overflow-hidden border border-[#E6DEC8] bg-white">
                <img src={preview || fileUrl(form.image)} alt="preview" className="w-full h-full object-cover" />
              </div>
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
            <Button onClick={save} disabled={saving} className="rounded-full bg-espresso hover:bg-espresso-soft text-cream px-6" data-testid="admin-idea-save-button">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : editing ? "Save Changes" : "Add to Website"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
