import Link from "next/link";

import { FOOTER, FOOTER_SOCIALS } from "../constants";

/* Brand icons drawn inline (lucide no longer ships brand marks). */
function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden>
      <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden>
      <path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z" />
    </svg>
  );
}

function LinkedInIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden>
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z" />
    </svg>
  );
}

const SOCIAL_ICONS = {
  github: GitHubIcon,
  twitter: XIcon,
  linkedin: LinkedInIcon,
} as const;

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="relative mt-4 overflow-hidden border-t border-border bg-card/30">
      {/* Light beam sliding along the top edge */}
      <div
        aria-hidden
        className="animate-beam-x absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,var(--color-primary),var(--color-info),var(--color-ai),transparent)] opacity-50"
      />
      {/* Calm background: faint dots + a single glow */}
      <div
        aria-hidden
        className="dot-grid absolute inset-0 opacity-40 [mask-image:radial-gradient(ellipse_70%_80%_at_50%_0%,black_10%,transparent_70%)]"
      />
      <div
        aria-hidden
        className="animate-drift absolute -top-20 left-1/4 h-56 w-96 rounded-full bg-primary/8 blur-3xl"
      />

      <div className="relative mx-auto w-full max-w-6xl px-4 pb-10 pt-14">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(4,1fr)]">
          {/* Brand */}
          <div>
            <Link href="/" className="flex items-center gap-2">
              <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
                SV
              </span>
              <span className="text-sm font-semibold">{FOOTER.copyright}</span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              {FOOTER.tagline}
            </p>
            <div className="mt-5 flex items-center gap-1">
              {FOOTER_SOCIALS.map((s) => {
                const Icon = SOCIAL_ICONS[s.icon];
                return (
                  <a
                    key={s.label}
                    href={s.href}
                    aria-label={s.label}
                    className="flex size-8 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors duration-200 hover:border-primary/40 hover:text-foreground"
                  >
                    <Icon className="size-4" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Link groups */}
          {FOOTER.groups.map((group) => (
            <nav key={group.title} aria-label={group.title}>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {group.title}
              </h3>
              <ul className="mt-4 space-y-2.5">
                {group.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground transition-colors duration-150 hover:text-foreground"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        {/* Disclaimer + bottom bar */}
        <div
          id="disclaimer"
          className="mt-12 scroll-mt-24 rounded-xl border border-gold/25 bg-gold/5 px-4 py-3"
        >
          <p className="text-xs leading-relaxed text-muted-foreground">
            {FOOTER.disclaimer}
          </p>
        </div>

        <div className="mt-8 flex flex-col items-center justify-between gap-3 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row">
          <p>
            © {year} {FOOTER.copyright}. For research and education only.
          </p>
          <p className="font-mono">NSE · BSE · Made in India</p>
        </div>
      </div>
    </footer>
  );
}
