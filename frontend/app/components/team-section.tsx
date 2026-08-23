import { TEAM_MEMBERS } from "../constants";

/** Team grid — placeholders driven entirely by constants.ts. */
export function TeamSection() {
  return (
    <section id="team" className="mx-auto w-full max-w-6xl px-4 py-20">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
          Team
        </p>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight sm:text-3xl">
          Built by a small team of builders
        </h2>
        <p className="mt-3 text-sm text-muted-foreground sm:text-base">
          Final-year project, open-source heart — meet the people behind
          StockView India.
        </p>
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {TEAM_MEMBERS.map((m, i) => (
          <article
            key={m.name}
            className="group rounded-2xl border border-border bg-card/60 p-6 text-center transition-colors duration-200 hover:border-primary/40"
            style={{ animationDelay: `${i * 70}ms` }}
          >
            <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-gradient-to-br from-primary to-info font-mono text-lg font-semibold text-white">
              {m.name
                .split(" ")
                .map((w) => w[0])
                .slice(0, 2)
                .join("")
                .toUpperCase()}
            </div>
            <h3 className="mt-4 font-medium">{m.name}</h3>
            <p className="mt-0.5 text-xs font-medium uppercase tracking-wide text-primary">
              {m.role}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">{m.bio}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
