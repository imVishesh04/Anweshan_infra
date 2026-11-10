import { useEffect } from "react";
import Lenis from "lenis";
import { SiteProvider } from "@/lib/SiteContext";
import Navbar from "@/sections/Navbar";
import Hero from "@/sections/Hero";
import Marquee from "@/sections/Marquee";
import Services from "@/sections/Services";
import Gallery from "@/sections/Gallery";
import Estimator from "@/sections/Estimator";
import Process from "@/sections/Process";
import Contact from "@/sections/Contact";
import Footer from "@/sections/Footer";
import MobileBar from "@/components/MobileBar";

export default function Home() {
  useEffect(() => {
    const lenis = new Lenis({ lerp: 0.09, smoothWheel: true });
    window.__lenis = lenis;
    let raf;
    const loop = (t) => {
      lenis.raf(t);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(raf);
      lenis.destroy();
      window.__lenis = null;
    };
  }, []);

  return (
    <SiteProvider>
      <div className="min-h-screen bg-cream text-espresso pb-[76px] md:pb-0">
        <Navbar />
        <main>
          <Hero />
          <Marquee />
          <Services />
          <Gallery />
          <Estimator />
          <Process />
          <Contact />
        </main>
        <Footer />
        <MobileBar />
      </div>
    </SiteProvider>
  );
}
