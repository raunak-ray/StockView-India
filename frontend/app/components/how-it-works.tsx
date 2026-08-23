import { HOW_IT_WORKS_STEPS } from "../constants";

export function HowItWorksSection() {
  return (
    <section id="how" className="border-y border-border bg-card/30">
      <div className="mx-auto w-full max-w-6xl px-4 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
            How it works
          </p>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight sm:text-3xl">
            From ticker to verdict in four steps
          </h2>
        </div>

        <ol className="mt-10 grid gap-4 sm:grid-cols-4">
          {HOW_IT_WORKS_STEPS.map(([step, title, desc], i) => (
            <li
              key={step}
              className="relative rounded-2xl border border-border bg-card/70 p-5"
            >
              {/* Connector */}
              {i < HOW_IT_WORKS_STEPS.length - 1 ? (
                <span
                  aria-hidden
                  className="absolute -right-4 top-1/2 hidden h-px w-8 bg-border sm:block"
                />
              ) : null}
              <span className="font-mono text-xs font-semibold text-primary">
                {step}
              </span>
              <h3 className="mt-2 font-medium">{title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
