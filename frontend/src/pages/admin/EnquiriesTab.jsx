import { useEffect, useState } from "react";
import { Check, Loader2, Phone, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { adminApi, formatApiError, formatDate, telHref, waLink } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { WhatsAppIcon } from "@/components/Logo";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function EnquiriesTab() {
  const [enquiries, setEnquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const load = async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      const r = await adminApi({ url: "/admin/enquiries" });
      setEnquiries(Array.isArray(r.data) ? r.data : []);
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // New enquiries show up when the owner comes back to this tab or app.
    const onFocus = () => load(true);
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);

  const unread = enquiries.filter((e) => !e.read).length;

  const markRead = async (eq) => {
    if (busyId) return;
    setBusyId(eq.id);
    try {
      await adminApi({ url: `/admin/enquiries/${eq.id}/read`, method: "PUT" });
      setEnquiries((list) => list.map((e) => (e.id === eq.id ? { ...e, read: true } : e)));
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (eq) => {
    if (busyId) return;
    setBusyId(eq.id);
    try {
      await adminApi({ url: `/admin/enquiries/${eq.id}`, method: "DELETE" });
      toast.success("Enquiry removed.");
      setEnquiries((list) => list.filter((e) => e.id !== eq.id));
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return <div className="grid place-items-center py-16"><Loader2 className="w-7 h-7 animate-spin text-brass" /></div>;
  }

  return (
    <div>
      <h2 className="font-serif text-2xl">
        Customer Enquiries
        {unread > 0 && (
          <span className="ml-2 align-middle inline-flex items-center rounded-full bg-terracotta text-white text-xs font-bold px-2.5 py-1">{unread} new</span>
        )}
      </h2>
      <p className="text-sm text-espresso-muted mt-0.5">Everyone who filled the form on your website. Call or WhatsApp them back.</p>

      {enquiries.length === 0 ? (
        <div className="mt-8 rounded-2xl border border-dashed border-[#E6DEC8] p-10 text-center text-espresso-muted">
          No enquiries yet. They will appear here the moment a customer fills the form.
        </div>
      ) : (
        <div className="mt-7 space-y-3.5" data-testid="admin-enquiries-list">
          {enquiries.map((eq) => (
            <div
              key={eq.id}
              className={`rounded-2xl border bg-card p-5 ${eq.read ? "border-[#E6DEC8]" : "border-brass/50 shadow-brass/20"}`}
              data-testid={`admin-enquiry-${eq.id}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2.5">
                    {!eq.read && <span className="w-2 h-2 rounded-full bg-brass animate-slow-pulse" data-testid={`enquiry-unread-dot-${eq.id}`} />}
                    <h3 className="font-serif text-xl">{eq.name}</h3>
                    {eq.service && (
                      <span className="text-[10px] font-bold uppercase tracking-[0.15em] bg-cream-alt text-espresso-muted rounded-full px-2.5 py-1">
                        {eq.service}
                      </span>
                    )}
                    {eq.source === "whatsapp" && (
                      <span className="text-[10px] font-bold uppercase tracking-[0.15em] bg-[#DCF8C6] text-[#075E54] rounded-full px-2.5 py-1" data-testid={`enquiry-source-${eq.id}`}>
                        WhatsApp
                      </span>
                    )}
                  </div>
                  <p className="mt-1.5 text-sm text-espresso-muted">{formatDate(eq.created_at)}</p>
                  {eq.message && <p className="mt-2 text-sm text-espresso leading-relaxed whitespace-pre-line">"{eq.message}"</p>}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <a
                    href={telHref(eq.phone)}
                    className="inline-flex items-center gap-1.5 rounded-full border border-espresso/25 text-espresso px-4 h-10 text-sm font-bold hover:bg-espresso hover:text-cream transition-colors"
                    data-testid={`enquiry-call-${eq.id}`}
                  >
                    <Phone className="w-4 h-4" /> {eq.phone}
                  </a>
                  <a
                    href={waLink(eq.phone, `Hello ${eq.name}! This is ANWESHAN Infra. Thank you for your enquiry${eq.service ? ` about ${eq.service}` : ""}. When is a good time to talk?`)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-full bg-wa hover:bg-wa-dark text-white px-4 h-10 text-sm font-bold transition-colors"
                    data-testid={`enquiry-whatsapp-${eq.id}`}
                  >
                    <WhatsAppIcon className="w-4 h-4" /> Reply
                  </a>
                  {!eq.read && (
                    <Button variant="outline" size="icon" className="h-10 w-10 rounded-full border-[#E6DEC8]" onClick={() => markRead(eq)} aria-label="Mark as read" data-testid={`enquiry-mark-read-${eq.id}`}>
                      <Check className="w-4 h-4" />
                    </Button>
                  )}
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-10 w-10 rounded-full text-terracotta hover:text-terracotta" aria-label="Delete enquiry" data-testid={`enquiry-delete-${eq.id}`}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent className="bg-cream border-[#E6DEC8]">
                      <AlertDialogHeader>
                        <AlertDialogTitle className="font-serif">Delete enquiry from {eq.name}?</AlertDialogTitle>
                        <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel className="rounded-full">Keep it</AlertDialogCancel>
                        <AlertDialogAction onClick={() => remove(eq)} className="rounded-full bg-terracotta hover:bg-terracotta/90">Delete</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
