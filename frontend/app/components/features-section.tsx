import { FEATURES } from "../constants";

export function FeaturesSection() {
  return (
    <section id="features" className="mx-auto w-full max-w-6xl px-4 py-20">
      <h2 className="text-center text-2xl font-semibold sm:text-3xl">
        Everything a trader needs
      </h2>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="group rounded-xl border border-border bg-card/50 p-6 transition-colors hover:border-primary/40"
          >
            <f.icon className="size-5 text-primary" />
            <h3 className="mt-4 font-semibold">{f.title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
