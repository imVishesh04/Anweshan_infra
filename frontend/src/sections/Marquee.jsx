const ITEMS = [
  "Architectural Residences",
  "Boutique Stores",
  "Custom Furniture",
  "Furniture Restoration",
  "3D Design First",
  "Design Of Your Choice",
];

export default function Marquee() {
  return (
    <div className="relative border-b border-[#E6DEC8] bg-cream-alt py-5 overflow-hidden" data-testid="marquee-strip">
      <div className="flex w-max animate-marquee hover:[animation-play-state:paused]">
        {[0, 1].map((dup) => (
          <div key={dup} aria-hidden={dup === 1} className="flex items-center shrink-0">
            {ITEMS.map((item) => (
              <span key={item} className="flex items-center">
                <span className="px-8 font-serif italic text-xl sm:text-2xl text-espresso/85 whitespace-nowrap">
                  {item}
                </span>
                <span className="w-2 h-2 rotate-45 bg-brass shrink-0" aria-hidden="true" />
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
