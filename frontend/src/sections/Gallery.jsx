import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Armchair, Home, LayoutGrid, Store } from "lucide-react";
import { api, imgUrl, waLink } from "@/lib/api";
import { useSite } from "@/lib/SiteContext";
import { WhatsAppIcon } from "../components/Logo";
import Reveal, { EASE, Eyebrow } from "../components/Reveal";

const FILTERS = [
  { v: "all", label: "All", icon: LayoutGrid },
  { v: "homes", label: "Homes", icon: Home },
  { v: "shops", label: "Shops", icon: Store },
  { v: "furniture", label: "Furniture", icon: Armchair },
];

const CAT_LABEL = { homes: "Home", shops: "Shop", furniture: "Furniture" };

export default function Gallery() {
  const { site } = useSite();
  const [filter, setFilter] = useState("all");
  const [ideas, setIdeas] = useState([]);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const load = useCallback(() => {
    setReady(false);
    setFailed(false);
    api
      .get("/ideas")
      .then((r) => setIdeas(Array.isArray(r.data) ? r.data : []))
      .catch(() => setFailed(true))
      .finally(() => setReady(true));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const PAGE = 12;
  const matching = filter === "all" ? ideas : ideas.filter((i) => i.category === filter);
  const shown = showAll ? matching : matching.slice(0, PAGE);

  return (
    <section id="ideas" className="relative py-20 sm:py-24 lg:py-28 bg-espresso text-cream grain" data-testid="gallery-section">
      <div className="relative z-10 max-w-7xl mx-auto px-5 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <Reveal>
            <Eyebrow light>Design ideas</Eyebrow>
            <h2 className="mt-4 font-serif text-4xl sm:text-5xl tracking-tight leading-[1.08]">
              Designs you can have —<br className="hidden sm:block" /> tap one you love.
            </h2>
          </Reveal>
          <Reveal delay={0.1} className="max-w-sm">
            <p className="text-cream/70 text-base sm:text-lg leading-relaxed">
              New designs are added by the studio every week. Found one you like? One tap and it is in your WhatsApp.
            </p>
          </Reveal>
        </div>

        <Reveal delay={0.15} className="mt-10 flex flex-wrap gap-2.5">
          {FILTERS.map(({ v, label, icon: Icon }) => (
            <button
              key={v}
              aria-pressed={filter === v}
              onClick={() => {
                setFilter(v);
                setShowAll(false);
              }}
              className={`inline-flex items-center gap-2 rounded-full px-5 h-11 text-sm font-bold transition-all ${
                filter === v
                  ? "bg-brass text-espresso shadow-brass"
                  : "border border-cream/25 text-cream/80 hover:border-brass hover:text-brass-light"
              }`}
              data-testid={`gallery-filter-${v}`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </Reveal>

        {!ready && (
          <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-5 lg:gap-6" aria-hidden="true">
            {[0, 1, 2].map((n) => (
              <div key={n} className="aspect-[4/5] rounded-[24px] bg-cream/5 animate-pulse" />
            ))}
          </div>
        )}

        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-5 lg:gap-6">
          <AnimatePresence initial={false}>
            {shown.map((idea, idx) => (
              <motion.article
                key={idea.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3, ease: EASE }}
                className="group relative aspect-[4/5] rounded-[24px] overflow-hidden border border-cream/10"
                data-testid="design-idea-card"
              >
                {idea.image ? (
                <img
                  src={imgUrl(idea.image, 900)}
                  decoding="async"
                  alt={idea.title}
                  loading="lazy"
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                ) : (
                  <div className="absolute inset-0 bg-espresso-soft" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-espresso via-espresso/15 to-transparent" />
                <span className="absolute top-4 left-4 rounded-full bg-espresso/45 border border-cream/25 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-cream/90">
                  {CAT_LABEL[idea.category] || idea.category}
                </span>
                <div className="absolute inset-x-0 bottom-0 p-5 flex items-end justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="font-serif text-xl text-cream truncate">{idea.title}</h3>
                    {idea.description && (
                      <p className="mt-1 text-sm text-cream/70 line-clamp-2">{idea.description}</p>
                    )}
                  </div>
                  <a
                    href={waLink(
                      site.whatsapp,
                      `Hi Anweshan Infra! I loved your "${idea.title}" design. Can we do something like this for my space?`
                    )}
                    target="_blank"
                    rel="noreferrer"
                    className="shrink-0 grid place-items-center w-11 h-11 rounded-full bg-wa hover:bg-wa-dark text-white shadow-brass transition-colors"
                    aria-label={`Ask about ${idea.title}`}
                    data-testid={`idea-ask-${idx}`}
                  >
                    <WhatsAppIcon className="w-5 h-5" />
                  </a>
                </div>
              </motion.article>
            ))}
          </AnimatePresence>
        </div>

        {ready && !showAll && matching.length > PAGE && (
          <div className="mt-8 text-center">
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className="inline-flex items-center rounded-full border border-cream/30 px-6 h-11 text-sm font-bold text-cream hover:border-brass hover:text-brass-light"
            >
              Show more designs ({matching.length - PAGE})
            </button>
          </div>
        )}

        {ready && failed && (
          <div className="mt-10 rounded-[24px] border border-dashed border-cream/20 p-10 text-center text-cream/70">
            Could not load designs. Please check your internet.
            <div className="mt-4">
              <button type="button" onClick={load} className="inline-flex items-center rounded-full bg-brass text-espresso px-6 h-11 text-sm font-bold">
                Tap to try again
              </button>
            </div>
          </div>
        )}

        {ready && !failed && matching.length === 0 && (
          <div className="mt-10 rounded-[24px] border border-dashed border-cream/20 p-12 text-center text-cream/60">
            No ideas here yet — new designs are being added. Please check again soon!
          </div>
        )}
      </div>
    </section>
  );
}
