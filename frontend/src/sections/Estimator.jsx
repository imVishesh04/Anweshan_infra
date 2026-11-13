import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BedDouble, CookingPot, DoorClosed, Hammer, Home, Paintbrush, RotateCcw,
  Sofa, UtensilsCrossed, Wrench,
} from "lucide-react";
import { useSite } from "@/lib/SiteContext";
import { waLink, withRef } from "@/lib/api";
import { WhatsAppIcon } from "../components/Logo";
import Reveal, { EASE, Eyebrow } from "../components/Reveal";

const TYPES = [
  { id: "sofa", label: "Sofa / Seating", icon: Sofa },
  { id: "bed", label: "Bed", icon: BedDouble },
  { id: "wardrobe", label: "Wardrobe", icon: DoorClosed },
  { id: "dining", label: "Dining Table", icon: UtensilsCrossed },
  { id: "kitchen", label: "Kitchen Cabinets", icon: CookingPot },
  { id: "room", label: "Full Room", icon: Home },
];

const NEEDS = [
  { id: "polish", label: "Polish & refresh", icon: Paintbrush },
  { id: "repair", label: "Repair & fix", icon: Wrench },
  { id: "remake", label: "Full remake", icon: Hammer },
];



export default function Estimator() {
  const { site } = useSite();
  const [type, setType] = useState(null);
  const [need, setNeed] = useState(null);

  const typeLabel = TYPES.find((t) => t.id === type)?.label;
  const needLabel = NEEDS.find((n) => n.id === need)?.label;

  const step = !type ? 1 : !need ? 2 : 3;

  return (
    <section id="estimate" className="py-20 sm:py-24 lg:py-28 bg-cream-alt" data-testid="estimator-section">
      <div className="max-w-3xl mx-auto px-5 lg:px-8">
        <Reveal className="text-center">
          <Eyebrow>Furniture assessment</Eyebrow>
          <h2 className="mt-4 font-serif text-4xl sm:text-5xl tracking-tight text-espresso leading-[1.08]">
            Not sure what your furniture needs? Tap and see.
          </h2>
          <p className="mt-4 text-espresso-muted text-base sm:text-lg">
            Two taps — pick the item, pick what to do. We take it from there.
          </p>
        </Reveal>

        <Reveal delay={0.1} className="mt-10">
          <div className="rounded-[28px] border border-[#E6DEC8] bg-card shadow-card p-6 sm:p-10">
            <div className="flex items-center justify-center gap-2 mb-8">
              {[1, 2, 3].map((n) => (
                <span
                  key={n}
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    n < step ? "w-10 bg-brass" : n === step ? "w-14 bg-espresso" : "w-10 bg-[#E6DEC8]"
                  }`}
                />
              ))}
            </div>

            <AnimatePresence mode="wait">
              {!type && (
                <motion.div key="type" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -14 }} transition={{ duration: 0.35, ease: EASE }}>
                  <p className="font-serif text-2xl text-espresso mb-5">1. What should we look at?</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {TYPES.map(({ id, label, icon: Icon }) => (
                      <button
                        key={id}
                        onClick={() => setType(id)}
                        className="flex flex-col items-center gap-2.5 rounded-2xl border border-[#E6DEC8] bg-cream p-4 text-espresso hover:border-brass hover:shadow-brass transition-all"
                        data-testid={`furniture-estimator-card-${id}`}
                      >
                        <Icon className="w-7 h-7 text-brass-dark" />
                        <span className="text-sm font-bold text-center leading-tight">{label}</span>
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}

              {type && !need && (
                <motion.div key="need" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -14 }} transition={{ duration: 0.35, ease: EASE }}>
                  <p className="font-serif text-2xl text-espresso mb-1">
                    2. What should we do with your <span className="text-brass-dark">{typeLabel}</span>?
                  </p>
                  <div className="grid sm:grid-cols-3 gap-3 mt-5">
                    {NEEDS.map(({ id, label, icon: Icon }) => (
                      <button
                        key={id}
                        onClick={() => setNeed(id)}
                        className="flex flex-col items-center gap-2.5 rounded-2xl border border-[#E6DEC8] bg-cream p-5 text-espresso hover:border-brass hover:shadow-brass transition-all"
                        data-testid={`estimator-need-${id}`}
                      >
                        <Icon className="w-7 h-7 text-brass-dark" />
                        <span className="text-sm font-bold text-center leading-tight">{label}</span>
                      </button>
                    ))}
                  </div>
                  <button onClick={() => setType(null)} className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-espresso-muted hover:text-espresso" data-testid="estimator-back-type">
                    <RotateCcw className="w-4 h-4" /> Choose a different item
                  </button>
                </motion.div>
              )}

              {type && need && (
                <motion.div key="result" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: EASE }} className="text-center">
                  <p className="text-sm font-bold uppercase tracking-[0.2em] text-espresso-muted">
                    {typeLabel} · {needLabel}
                  </p>
                  <p className="mt-3 font-serif text-3xl sm:text-4xl text-espresso leading-snug" data-testid="estimator-result-range">
                    We'll inspect and tell you the honest price.
                  </p>
                  <p className="mt-3 text-sm text-espresso-muted max-w-md mx-auto">
                    No guessing — final price only after we see your furniture in person.
                  </p>
                  <div className="mt-7 flex flex-col sm:flex-row justify-center gap-3">
                    <a
                      href={waLink(
                        site.whatsapp,
                        withRef(`Hi Anweshan Infra! I used your Furniture Assessment tool.\nItem: ${typeLabel}\nNeed: ${needLabel}\nPlease guide me.`, "AI-FURNITURE")
                      )}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(e) => { if (!site.whatsapp) e.preventDefault(); }}
                      className="inline-flex items-center justify-center gap-2.5 rounded-full bg-wa hover:bg-wa-dark text-white px-7 h-13 h-[52px] font-bold shadow-brass transition-colors"
                      data-testid="estimator-whatsapp-button"
                    >
                      <WhatsAppIcon className="w-5 h-5" /> Send my assessment
                    </a>
                    <button
                      onClick={() => { setType(null); setNeed(null); }}
                      className="inline-flex items-center justify-center gap-2 rounded-full border border-espresso/25 text-espresso px-7 h-[52px] font-bold hover:bg-espresso hover:text-cream transition-colors"
                      data-testid="estimator-reset-button"
                    >
                      <RotateCcw className="w-4 h-4" /> Start again
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
