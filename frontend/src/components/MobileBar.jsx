import { Phone } from "lucide-react";
import { telHref, waLink } from "@/lib/api";
import { useSite } from "@/lib/SiteContext";
import { WhatsAppIcon } from "./Logo";

export default function MobileBar() {
  const { site } = useSite();

  return (
    <div
      className="fixed bottom-0 inset-x-0 z-50 md:hidden bg-cream border-t border-[#E6DEC8] px-3 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]"
      data-testid="mobile-sticky-bar"
    >
      <div className="grid grid-cols-2 gap-2.5">
        <a
          href={site.phone ? telHref(site.phone) : "#contact"}
          className="inline-flex items-center justify-center gap-2 h-12 rounded-full bg-espresso text-cream font-bold text-sm"
          data-testid="mobile-sticky-call-btn"
        >
          <Phone className="w-4 h-4" /> Call Now
        </a>
        <a
          href={site.whatsapp ? waLink(site.whatsapp, "Hi Anweshan Infra! I want to design my space. Please guide me.") : "#contact"}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center justify-center gap-2 h-12 rounded-full bg-wa text-white font-bold text-sm"
          data-testid="mobile-sticky-whatsapp-btn"
        >
          <WhatsAppIcon className="w-4 h-4" /> WhatsApp Us
        </a>
      </div>
    </div>
  );
}
