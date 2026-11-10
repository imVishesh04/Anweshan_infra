import { useState } from "react";
import { ChevronDown, Clock, Instagram, MapPin, Phone, User } from "lucide-react";
import { toast } from "sonner";
import { api, formatApiError, instagramUrl, telHref, waLink } from "@/lib/api";
import { useSite } from "@/lib/SiteContext";
import Logo, { WhatsAppIcon } from "../components/Logo";
import Reveal, { Eyebrow } from "../components/Reveal";

export default function Contact() {
  const { site, services } = useSite();
  const [form, setForm] = useState({ name: "", phone: "", service: "", message: "" });
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    // Same rules as the server, so customers see the problem right under the form.
    const name = form.name.trim();
    const phone = form.phone.trim();
    const phoneDigits = phone.replace(/\D/g, "");
    if (name.length < 2) return setError("Please enter your name.");
    if (name.length > 80) return setError("Name is too long (max 80 letters).");
    if (!/^[0-9+\-(). ]+$/.test(phone) || phoneDigits.length < 10 || phoneDigits.length > 13) {
      return setError("Please enter a valid 10-digit phone number.");
    }
    setSending(true);
    try {
      await api.post("/enquiries", { ...form, name, phone });
      toast.success("Thank you! We will call you soon.");
      setForm({ name: "", phone: "", service: "", message: "" });
    } catch (err) {
      const msg = formatApiError(err, "Could not send. Please WhatsApp us instead.");
      setError(msg);
      toast.error(msg);
    } finally {
      setSending(false);
    }
  };

  const tiles = [
    site.whatsapp && {
      key: "whatsapp",
      href: waLink(site.whatsapp, "Hi Anweshan Infra! I want to design my space. Please guide me."),
      icon: <WhatsAppIcon className="w-7 h-7" />,
      title: "WhatsApp",
      sub: "Fastest reply — tap and type",
      cls: "bg-wa hover:bg-wa-dark text-white",
      testid: "contact-tile-whatsapp",
    },
    site.phone && {
      key: "call",
      href: telHref(site.phone),
      icon: <Phone className="w-7 h-7" />,
      title: "Phone Call",
      sub: site.phone,
      cls: "bg-cream/10 hover:bg-cream/20 text-cream border border-cream/25",
      testid: "contact-tile-call",
    },
    site.instagram && {
      key: "instagram",
      href: instagramUrl(site.instagram),
      icon: <Instagram className="w-7 h-7" />,
      title: "Instagram",
      sub: "See our latest work",
      cls: "bg-cream/10 hover:bg-cream/20 text-cream border border-cream/25",
      testid: "contact-tile-instagram",
    },
  ].filter(Boolean);

  return (
    <section id="contact" className="relative py-20 sm:py-24 lg:py-28 bg-espresso text-cream grain" data-testid="contact-section">
      <div className="relative z-10 max-w-7xl mx-auto px-5 lg:px-8 grid lg:grid-cols-2 gap-12 lg:gap-16 items-start">
        <div>
          <Reveal>
            <Eyebrow light>Contact</Eyebrow>
            <h2 className="mt-4 font-serif text-4xl sm:text-5xl tracking-tight leading-[1.08]">
              Talk to us —<br /> it&rsquo;s easy.
            </h2>
            <p className="mt-5 text-cream/75 text-base sm:text-lg leading-relaxed max-w-md">
              Tap one button below and we take it from there. Prefer writing? Use the form and we will call you back.
            </p>
          </Reveal>

          <div className="mt-9 grid sm:grid-cols-2 gap-3.5">
            {tiles.map((t) => (
              <a
                key={t.key}
                href={t.href}
                target={t.href.startsWith("http") ? "_blank" : undefined}
                rel="noreferrer"
                className={`flex items-center gap-4 rounded-[22px] px-6 py-5 transition-colors ${t.cls}`}
                data-testid={t.testid}
              >
                <span className="shrink-0">{t.icon}</span>
                <span className="min-w-0">
                  <span className="block font-bold text-lg leading-tight">{t.title}</span>
                  <span className="block text-sm opacity-75 truncate">{t.sub}</span>
                </span>
              </a>
            ))}
          </div>

          {(site.address || site.hours) && (
            <Reveal delay={0.1} className="mt-4 space-y-2 text-cream/70 text-sm">
              {site.address && (
                <p className="flex items-start gap-2.5">
                  <MapPin className="w-4 h-4 mt-0.5 text-brass-light shrink-0" /> {site.address}
                </p>
              )}
              {site.hours && (
                <p className="flex items-start gap-2.5">
                  <Clock className="w-4 h-4 mt-0.5 text-brass-light shrink-0" /> {site.hours}
                </p>
              )}
            </Reveal>
          )}

          <Reveal delay={0.15} className="mt-8">
            <Logo light />
          </Reveal>
        </div>

        <Reveal delay={0.1}>
          <form
            onSubmit={submit}
            className="rounded-[28px] bg-cream text-espresso p-6 sm:p-9 shadow-card"
            data-testid="contact-form"
          >
            <h3 className="font-serif text-3xl">Send an enquiry</h3>
            <p className="mt-1.5 text-sm text-espresso-muted">Fill 2 fields, press send. We call you back.</p>

            <div className="mt-7 space-y-5">
              <div>
                <label htmlFor="cf-name" className="flex items-center gap-2 text-sm font-bold text-espresso">
                  <User className="w-4 h-4 text-brass-dark" /> Your Name *
                </label>
                <input
                  id="cf-name"
                  value={form.name}
                  onChange={set("name")}
                  name="name"
                  autoComplete="name"
                  maxLength={80}
                  placeholder="e.g. Priya Sharma"
                  className="mt-2 w-full h-12 rounded-xl border border-[#E6DEC8] bg-white px-4 text-base outline-none focus:border-brass focus:ring-2 focus:ring-brass/30 transition"
                  data-testid="contact-form-name-input"
                />
              </div>

              <div>
                <label htmlFor="cf-phone" className="flex items-center gap-2 text-sm font-bold text-espresso">
                  <Phone className="w-4 h-4 text-brass-dark" /> Phone Number *
                </label>
                <input
                  id="cf-phone"
                  type="tel"
                  inputMode="tel"
                  value={form.phone}
                  onChange={set("phone")}
                  name="phone"
                  autoComplete="tel"
                  maxLength={20}
                  placeholder="e.g. 98765 43210"
                  className="mt-2 w-full h-12 rounded-xl border border-[#E6DEC8] bg-white px-4 text-base outline-none focus:border-brass focus:ring-2 focus:ring-brass/30 transition"
                  data-testid="contact-form-phone-input"
                />
              </div>

              <div>
                <label htmlFor="cf-service" className="flex items-center gap-2 text-sm font-bold text-espresso">
                  <MapPin className="w-4 h-4 text-brass-dark" /> What do you need?
                </label>
                <div className="relative mt-2">
                  <select
                    id="cf-service"
                    value={form.service}
                    onChange={set("service")}
                    className="w-full h-12 rounded-xl border border-[#E6DEC8] bg-white pl-4 pr-10 text-base outline-none focus:border-brass focus:ring-2 focus:ring-brass/30 transition appearance-none"
                    data-testid="contact-form-service-select"
                  >
                    <option value="">Choose one…</option>
                    {services.map((s) => (
                      <option key={s.id} value={s.title}>{s.title}</option>
                    ))}
                    <option value="Something else">Something else</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-espresso-muted absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              <div>
                <label htmlFor="cf-message" className="block text-sm font-bold text-espresso">
                  Your message <span className="font-normal text-espresso-muted">(optional)</span>
                </label>
                <textarea
                  id="cf-message"
                  value={form.message}
                  onChange={set("message")}
                  maxLength={1000}
                  rows={3}
                  placeholder="Tell us about your space…"
                  className="mt-2 w-full rounded-xl border border-[#E6DEC8] bg-white px-4 py-3 text-base outline-none focus:border-brass focus:ring-2 focus:ring-brass/30 transition resize-none"
                  data-testid="contact-form-message-input"
                />
              </div>

              {error && (
                <p role="alert" className="text-sm font-semibold text-terracotta" data-testid="contact-form-error">{error}</p>
              )}

              <button
                type="submit"
                disabled={sending}
                className="w-full h-13 h-[52px] rounded-full bg-espresso text-cream font-bold tracking-wide hover:bg-espresso-soft disabled:opacity-60 transition-all flex items-center justify-center gap-2.5"
                data-testid="contact-form-submit-button"
              >
                {sending ? "Sending…" : "Send Enquiry"}
              </button>
              <p className="text-center text-xs text-espresso-muted">
                We never share your number. We usually reply within a few hours.
              </p>
            </div>
          </form>
        </Reveal>
      </div>
    </section>
  );
}
