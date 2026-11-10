import { Instagram, Phone } from "lucide-react";
import { WhatsAppIcon } from "../components/Logo";
import { useSite } from "@/lib/SiteContext";
import { instagramUrl, scrollToId, telHref, waLink } from "@/lib/api";

export default function Footer() {
  const { site } = useSite();
  const year = new Date().getFullYear();

  return (
    <footer className="bg-[#120D0B] text-cream/60">
      <div className="max-w-7xl mx-auto px-5 lg:px-8 py-14">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-10">
          <div className="max-w-sm">
            <span className="inline-flex items-center gap-3">
              <img src="/logo-white.png" alt="" aria-hidden="true" className="w-11 h-11 -my-1 object-contain" />
              <span className="leading-none">
                <span className="block font-serif font-semibold tracking-[0.06em] text-lg text-cream">ANWESHAN</span>
                <span className="block text-[10px] font-sans font-semibold tracking-[0.5em] text-brass mt-1">INFRA</span>
              </span>
            </span>
            <p className="mt-4 text-sm leading-relaxed">
              Warm, elegant interiors for homes and shops — built with honest prices and one clear quote.
            </p>
          </div>

          <div className="flex flex-col gap-2.5">
            <p className="text-[11px] uppercase tracking-[0.3em] font-bold text-brass mb-1">Explore</p>
            {[["services", "Services"], ["ideas", "Design Ideas"], ["how", "How It Works"], ["contact", "Contact"]].map(([id, label]) => (
              <button key={id} onClick={() => scrollToId(id)} className="text-left text-sm min-h-[44px] hover:text-brass-light transition-colors w-fit">
                {label}
              </button>
            ))}
          </div>

          <div className="flex flex-col gap-3">
            <p className="text-[11px] uppercase tracking-[0.3em] font-bold text-brass mb-1">Reach us</p>
            <a href={site.whatsapp ? waLink(site.whatsapp, "Hi Anweshan Infra!") : "#contact"} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2.5 min-h-[44px] text-sm hover:text-brass-light transition-colors w-fit" data-testid="footer-whatsapp-link">
              <WhatsAppIcon className="w-4 h-4" /> WhatsApp us
            </a>
            <a href={site.phone ? telHref(site.phone) : "#contact"} className="inline-flex items-center gap-2.5 min-h-[44px] text-sm hover:text-brass-light transition-colors w-fit" data-testid="footer-call-link">
              <Phone className="w-4 h-4" /> {site.phone || "Call us"}
            </a>
            {site.instagram && (
              <a href={instagramUrl(site.instagram)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2.5 min-h-[44px] text-sm hover:text-brass-light transition-colors w-fit" data-testid="footer-instagram-link">
                <Instagram className="w-4 h-4" /> Instagram
              </a>
            )}
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-cream/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <p>© {year} ANWESHAN Infra · Interiors · Spaces · Lifestyle</p>
        </div>
      </div>
    </footer>
  );
}
