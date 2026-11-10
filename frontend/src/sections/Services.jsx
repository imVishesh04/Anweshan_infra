import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Armchair, Home, MessageCircle, Store, Timer } from "lucide-react";
import { useSite } from "@/lib/SiteContext";
import { waLink } from "@/lib/api";
import Reveal, { EASE, Eyebrow } from "../components/Reveal";

const ICONS = { home: Home, shop: Store, armchair: Armchair };

const slug = (t) => t.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

export default function Services() {
  const { site, services, ready } = useSite();

  return (
    <section id="services" className="py-20 sm:py-24 lg:py-28 bg-cream" data-testid="services-section">
      <div className="max-w-7xl mx-auto px-5 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <Reveal>
            <Eyebrow>What we do</Eyebrow>
            <h2 className="mt-4 font-serif text-4xl sm:text-5xl tracking-tight text-espresso leading-[1.08]">
              Three ways we make
              <br className="hidden sm:block" /> your space beautiful.
            </h2>
          </Reveal>
          <Reveal delay={0.1} className="max-w-sm">
            <p className="text-espresso-muted text-base sm:text-lg leading-relaxed">
              Pick what you need. Tap the button. We take it from there — simple as that.
            </p>
          </Reveal>
        </div>

        <div className="mt-12 lg:mt-16 grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {!ready &&
            [0, 1, 2].map((i) => (
              <div key={i} className="rounded-[28px] border border-[#E6DEC8] bg-card overflow-hidden">
                <div className="h-60 bg-cream-alt animate-pulse" />
                <div className="p-6 space-y-4">
                  <div className="h-6 w-2/3 bg-cream-alt rounded animate-pulse" />
                  <div className="h-4 w-full bg-cream-alt rounded animate-pulse" />
                  <div className="h-12 w-full bg-cream-alt rounded-full animate-pulse" />
                </div>
              </div>
            ))}

          {ready && services.length === 0 && (
            <div className="md:col-span-2 lg:col-span-3 rounded-[28px] border border-dashed border-[#E6DEC8] p-12 text-center text-espresso-muted">
              Services are being prepared. Please WhatsApp us — we reply fast.
            </div>
          )}

          {services.map((service, i) => {
            const Icon = ICONS[service.icon] || Home;
            const enquireText = `Hi Anweshan Infra! I am interested in "${service.title}". Please tell me more.`;
            return (
              <motion.article
                key={service.id}
                initial={{ opacity: 0, y: 32 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.15 }}
                transition={{ duration: 0.7, delay: i * 0.08, ease: EASE }}
                className="group flex flex-col rounded-[28px] border border-[#E6DEC8] bg-card overflow-hidden shadow-card hover:shadow-brass/40 transition-shadow"
                data-testid={`service-card-${slug(service.title)}`}
              >
                <div className="relative h-56 sm:h-60 overflow-hidden">
                  {service.image ? (
                    <img
                      src={service.image}
                      alt={service.title}
                      loading="lazy"
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                    />
                  ) : (
                    <div className="w-full h-full bg-cream-alt" />
                  )}
                  <span className="absolute top-4 left-4 inline-flex items-center gap-2 rounded-full bg-cream/90 backdrop-blur px-3.5 py-2 text-xs font-bold text-espresso shadow-sm">
                    <Icon className="w-4 h-4 text-brass-dark" />
                    {service.title}
                  </span>
                </div>

                <div className="flex flex-col flex-1 p-6">
                  {service.timeline && (
                    <span className="inline-flex w-fit items-center gap-1.5 text-xs font-semibold text-espresso-muted bg-cream-alt rounded-full px-3 py-1.5">
                      <Timer className="w-3.5 h-3.5" />
                      {service.timeline}
                    </span>
                  )}
                  <h3 className="mt-3 font-serif text-2xl text-espresso">{service.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-espresso-muted flex-1">{service.description}</p>
                  <a
                    href={site.whatsapp ? waLink(site.whatsapp, enquireText) : "#contact"}
                    onClick={(e) => {
                      if (!site.whatsapp) {
                        e.preventDefault();
                        document.getElementById("contact")?.scrollIntoView({ behavior: "smooth" });
                      }
                    }}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-5 inline-flex items-center justify-center gap-2.5 w-full h-12 rounded-full bg-espresso text-cream font-bold text-sm tracking-wide hover:bg-espresso-soft hover:shadow-brass transition-all"
                    data-testid={`service-enquire-${slug(service.title)}`}
                  >
                    <MessageCircle className="w-[18px] h-[18px]" />
                    Enquire for This Service
                  </a>
                </div>
              </motion.article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
