import { KeyRound, MapPin, MessageCircle, Ruler } from "lucide-react";
import Reveal, { Eyebrow } from "../components/Reveal";

const STEPS = [
  { icon: MessageCircle, title: "Tap WhatsApp or Call", text: "Tell us about your home, shop or furniture — in your own words. No paperwork." },
  { icon: MapPin, title: "We visit you — free", text: "We come to you, measure everything and listen to what you want and your budget." },
  { icon: Ruler, title: "See ideas & fixed price", text: "We show you 3D designs and one clear written price. No hidden charges, ever." },
  { icon: KeyRound, title: "We build & hand over", text: "Our own team completes the work on time and hands you the finished space." },
];

export default function Process() {
  return (
    <section id="how" className="py-20 sm:py-24 lg:py-28 bg-cream" data-testid="process-section">
      <div className="max-w-7xl mx-auto px-5 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <Reveal>
            <Eyebrow>How it works</Eyebrow>
            <h2 className="mt-4 font-serif text-4xl sm:text-5xl tracking-tight text-espresso leading-[1.08]">
              Four easy steps.
              <br className="hidden sm:block" /> From first message to finished space.
            </h2>
          </Reveal>
        </div>

        <div className="mt-12 lg:mt-16 grid sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-6">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <Reveal key={title} delay={i * 0.09}>
              <div className="relative h-full rounded-[24px] border border-[#E6DEC8] bg-card p-7">
                <span className="absolute top-5 right-6 font-serif italic text-6xl text-brass/25 select-none">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="grid place-items-center w-14 h-14 rounded-full bg-espresso text-brass-light">
                  <Icon className="w-6 h-6" />
                </span>
                <h3 className="mt-6 font-serif text-xl text-espresso pr-10">{title}</h3>
                <p className="mt-2.5 text-sm leading-relaxed text-espresso-muted">{text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
