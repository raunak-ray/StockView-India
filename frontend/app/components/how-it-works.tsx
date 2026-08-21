import { HOW_IT_WORKS_STEPS } from "../constants";

export function HowItWorksSection() {
  return (
    <section id="how" className="mx-auto w-full max-w-6xl px-4 pb-24">
      <div className="rounded-2xl border border-border bg-card/50 p-8 text-center sm:p-12">
        <h2 className="text-2xl font-semibold sm:text-3xl">
          From ticker to verdict in four steps
        </h2>
        <div className="mt-8 grid gap-4 text-left sm:grid-cols-4">
          {HOW_IT_WORKS_STEPS.map(([step, title, desc]) => (
            <div key={step} className="rounded-xl border border-border p-5">
              <span className="font-mono text-xs text-primary">{step}</span>
              <h3 className="mt-2 font-semibold">{title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
