import React from 'react';
import { Sparkles, ShieldCheck, Zap, Activity, Tag, ArrowRight } from 'lucide-react';

export default function HeroBanner({ categories, selectedCategory, onSelectCategory }) {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-950/60 via-slate-900/80 to-[#0A0E1A] border border-indigo-900/30 p-6 sm:p-10 mb-8 shadow-2xl">
      {/* Decorative ambient background glows */}
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="relative z-10 max-w-3xl">
        {/* Architecture Badges */}
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Distributed Saga Pattern
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            OpenTelemetry + Jaeger Tracing
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-medium">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            On-Screen OTP Login
          </span>
        </div>

        {/* Hero Title */}
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
          Enterprise Tech Hardware <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-indigo-400 via-indigo-300 to-emerald-400 bg-clip-text text-transparent">
            Engineered with Observability.
          </span>
        </h1>

        <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-6 max-w-2xl">
          Shop high-performance creator workstations, studio acoustics, and CNC mechanical keyboards.
          Every user interaction, catalog query, stock reservation, and payment transaction is traced end-to-end across 6 FastAPI microservices.
        </p>

        {/* Promo code callout banner */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-xs text-slate-300 mb-8">
          <Tag className="w-3.5 h-3.5 text-emerald-400" />
          <span>Demo Promo: Use voucher</span>
          <code className="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 font-mono font-bold">
            FASTAPI20
          </code>
          <span>for 20% off at checkout</span>
        </div>

        {/* Category Navigation Pills */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Explore Categories:
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => onSelectCategory(null)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all ${
                selectedCategory === null
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'bg-slate-800/70 text-slate-300 hover:bg-slate-700 border border-slate-700/60'
              }`}
            >
              All Catalog
            </button>
            {categories.map((cat) => (
              <button
                key={cat.uuid || cat.slug}
                onClick={() => onSelectCategory(cat.uuid || cat.slug)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all ${
                  selectedCategory === (cat.uuid || cat.slug)
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'bg-slate-800/70 text-slate-300 hover:bg-slate-700 border border-slate-700/60'
                }`}
              >
                {cat.name}
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

