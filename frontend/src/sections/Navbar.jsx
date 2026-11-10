import { useEffect, useState } from "react";
import { Menu, Phone, X } from "lucide-react";
import Logo, { WhatsAppIcon } from "../components/Logo";
import { useSite } from "@/lib/SiteContext";
import { scrollToId, telHref, waLink } from "@/lib/api";

const LINKS = [
  { id: "services", label: "Services" },
  { id: "ideas", label: "Design Ideas" },
  { id: "how", label: "How It Works" },
  { id: "contact", label: "Contact" },
];

export default function Navbar() {
  const { site } = useSite();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const go = (id) => {
    setOpen(false);
    setTimeout(() => scrollToId(id), 60);
  };

  const tone = scrolled || open ? "text-espresso" : "text-cream";

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-colors duration-500 ${
        scrolled
          ? "bg-cream/95 border-b border-[#E6DEC8]/70 shadow-sm"
          : "bg-transparent"
      } ${open ? "bg-cream border-b border-[#E6DEC8]" : ""}`}
    >
      <div className="max-w-7xl mx-auto px-5 lg:px-8 h-16 md:h-[76px] flex items-center justify-between">
        <button onClick={() => go("top")} className="shrink-0" data-testid="nav-brand-logo" aria-label="Anweshan Infra home">
          <Logo light={!scrolled && !open} />
        </button>

        <nav className={`hidden lg:flex items-center gap-8 ${tone}`}>
          {LINKS.map((l) => (
            <button
              key={l.id}
              onClick={() => go(l.id)}
              className={`text-sm font-semibold tracking-wide transition-colors hover:text-brass ${tone}`}
              data-testid={`nav-link-${l.id}`}
            >
              {l.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-2.5">
          <a
            href={site.phone ? telHref(site.phone) : "#contact"}
            onClick={(e) => { if (!site.phone) { e.preventDefault(); go("contact"); } }}
            className={`hidden sm:inline-flex items-center justify-center w-11 h-11 rounded-full border transition-colors ${
              scrolled || open ? "border-espresso/25 text-espresso hover:bg-espresso hover:text-cream" : "border-cream/35 text-cream hover:bg-cream hover:text-espresso"
              }`}
            aria-label="Call the studio"
            data-testid="nav-call-button"
          >
            <Phone className="w-4.5 h-4.5 w-[18px] h-[18px]" />
          </a>
          <a
            href={site.whatsapp ? waLink(site.whatsapp, "Hi Anweshan Infra! I want to design my space. Please guide me.") : "#contact"}
            onClick={(e) => { if (!site.whatsapp) { e.preventDefault(); go("contact"); } }}
            target="_blank"
            rel="noreferrer"
            className="hidden sm:inline-flex items-center gap-2 rounded-full bg-wa hover:bg-wa-dark text-white pl-4 pr-5 h-11 text-sm font-bold shadow-brass transition-colors"
            data-testid="nav-whatsapp-button"
          >
            <WhatsAppIcon className="w-4 h-4" />
            WhatsApp Us
          </a>
          <button
            onClick={() => setOpen(!open)}
            className={`lg:hidden inline-flex items-center justify-center w-11 h-11 rounded-full border ${scrolled || open ? "border-espresso/25 text-espresso" : "border-cream/35 text-cream"}`}
            aria-label="Open menu"
            data-testid="nav-menu-button"
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="lg:hidden bg-cream border-b border-[#E6DEC8] px-5 pb-6 pt-2 shadow-xl">
          <div className="flex flex-col gap-1">
            {LINKS.map((l) => (
              <button
                key={l.id}
                onClick={() => go(l.id)}
                className="text-left font-serif text-2xl text-espresso py-2.5 border-b border-[#E6DEC8]/60"
                data-testid={`nav-mobile-link-${l.id}`}
              >
                {l.label}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-2.5 mt-5">
            <a
              href={site.phone ? telHref(site.phone) : "#contact"}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-espresso text-cream h-12 font-semibold"
              data-testid="nav-mobile-call-button"
            >
              <Phone className="w-4 h-4" /> Call Now
            </a>
            <a
              href={site.whatsapp ? waLink(site.whatsapp, "Hi Anweshan Infra! I want to design my space. Please guide me.") : "#contact"}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-full bg-wa text-white h-12 font-semibold"
              data-testid="nav-mobile-whatsapp-button"
            >
              <WhatsAppIcon className="w-4 h-4" /> WhatsApp
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
