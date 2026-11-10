import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { ArrowDown, Ruler, ShieldCheck, Sparkles } from "lucide-react";
import { useSite } from "@/lib/SiteContext";
import { digits, waLink } from "@/lib/api";
import { WhatsAppIcon } from "../components/Logo";
import { EASE } from "../components/Reveal";

const HERO_BG =
  "https://images.unsplash.com/photo-1700226034367-2fb120f48dfa?crop=entropy&cs=srgb&fm=jpg&q=85";

const LINES = ["Spaces that", "feel like", "home."];

const CHIPS = [
  { icon: Sparkles, label: "Free first visit" },
  { icon: ShieldCheck, label: "Design of your choice" },
  { icon: Ruler, label: "3D design before work starts" },
];

export default function Hero() {
  const { site } = useSite();
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "18%"]);

  return (
    <section id="top" ref={ref} className="relative min-h-[100svh] flex items-end overflow-hidden bg-espresso">
      <motion.div style={{ y }} className="absolute inset-0 -bottom-[18%]">
        <img
          src={HERO_BG}
          alt="Warm elegant living room designed by Anweshan Infra"
          className="w-full h-full object-cover"
        />
      </motion.div>
      <div className="absolute inset-0 bg-gradient-to-b from-espresso/75 via-espresso/30 to-espresso/95" />
      <div className="absolute inset-0 bg-gradient-to-r from-espresso/65 via-espresso/20 to-transparent" />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-5 lg:px-8 pt-36 pb-20 md:pb-24">
        <motion.p
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: EASE }}
          className="text-[11px] sm:text-xs uppercase tracking-[0.32em] font-bold text-brass-light"
        >
          ANWESHAN Infra — Interiors · Spaces · Lifestyle
        </motion.p>

        <h1 className="mt-5 font-serif font-medium text-cream text-5xl sm:text-7xl lg:text-[6.2rem] leading-[1.04] tracking-tight">
          {LINES.map((line, i) => (
            <span key={line} className="mask-line">
              <motion.span
                className={`block ${i === 2 ? "italic text-brass-light" : ""}`}
                initial={{ y: "112%" }}
                animate={{ y: 0 }}
                transition={{ duration: 1, delay: 0.25 + i * 0.13, ease: EASE }}
              >
                {line}
              </motion.span>
            </span>
          ))}
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.75, ease: EASE }}
          className="mt-6 max-w-xl text-cream/80 text-base sm:text-lg leading-relaxed"
        >
          Warm, elegant interiors for homes and shops — designed, built and handed over by one team.
          You just tap a button and tell us your dream.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.9, ease: EASE }}
          className="mt-9 flex flex-col sm:flex-row gap-3.5"
        >
          <a
            href={site.whatsapp ? waLink(site.whatsapp, "Hi Anweshan Infra! I want to design my space. Please guide me.") : "#contact"}
            onClick={(e) => { if (!site.whatsapp) { e.preventDefault(); document.getElementById("contact")?.scrollIntoView({ behavior: "smooth" }); } }}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center gap-2.5 rounded-full bg-wa hover:bg-wa-dark text-white px-8 h-14 text-base font-bold shadow-brass transition-colors"
            data-testid="hero-whatsapp-cta"
          >
            <WhatsAppIcon className="w-5 h-5" />
            Chat on WhatsApp
          </a>
          <a
            href={site.phone ? `tel:${digits(site.phone)}` : "#contact"}
            onClick={(e) => { if (!site.phone) { e.preventDefault(); document.getElementById("contact")?.scrollIntoView({ behavior: "smooth" }); } }}
            className="inline-flex items-center justify-center gap-2.5 rounded-full border border-cream/40 bg-cream/10 backdrop-blur hover:bg-cream/20 text-cream px-8 h-14 text-base font-bold transition-colors"
            data-testid="hero-call-cta"
          >
            Call Now
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 1.1 }}
          className="mt-10 flex flex-wrap gap-2.5"
        >
          {CHIPS.map(({ icon: Icon, label }) => (
            <span
              key={label}
              className="inline-flex items-center gap-2 rounded-full border border-cream/25 bg-espresso/30 backdrop-blur px-4 py-2 text-xs sm:text-sm font-semibold text-cream/90"
            >
              <Icon className="w-4 h-4 text-brass-light" />
              {label}
            </span>
          ))}
        </motion.div>
      </div>

      <motion.button
        onClick={() => document.getElementById("services")?.scrollIntoView({ behavior: "smooth" })}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4, duration: 0.8 }}
        className="absolute bottom-6 right-8 z-10 hidden md:flex flex-col items-center gap-2 text-cream/70 hover:text-brass-light transition-colors"
        aria-label="Scroll to services"
        data-testid="hero-scroll-cue"
      >
        <span className="text-[10px] uppercase tracking-[0.3em]">Scroll</span>
        <motion.span animate={{ y: [0, 8, 0] }} transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}>
          <ArrowDown className="w-5 h-5" />
        </motion.span>
      </motion.button>
    </section>
  );
}
