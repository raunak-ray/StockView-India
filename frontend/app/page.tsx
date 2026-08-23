import { BentoFeatures } from "./components/bento-features";
import { CtaSection } from "./components/cta-section";
import { HeroSection } from "./components/hero-section";
import { HowItWorksSection } from "./components/how-it-works";
import { SiteFooter } from "./components/site-footer";
import { SiteHeader } from "./components/site-header";
import { TeamSection } from "./components/team-section";
import { MarketTickerMarquee } from "./components/ticker-marquee";

export default function LandingPage() {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <SiteHeader />

      <main className="flex-1">
        <HeroSection />
        <MarketTickerMarquee />
        <BentoFeatures />
        <HowItWorksSection />
        <TeamSection />
        <CtaSection />
      </main>

      <SiteFooter />
    </div>
  );
}
