import { motion } from "framer-motion";

export const EASE = [0.22, 1, 0.36, 1];

export default function Reveal({ children, delay = 0, y = 28, className = "", once = true }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once, amount: 0.15 }}
      transition={{ duration: 0.75, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}

export function Eyebrow({ children, light = false }) {
  return (
    <p className={`text-[11px] sm:text-xs uppercase tracking-[0.3em] font-sans font-bold ${light ? "text-brass-light" : "text-brass-dark"}`}>
      {children}
    </p>
  );
}
