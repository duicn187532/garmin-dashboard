import { Activity, Bot, CalendarDays, HeartPulse, LineChart, Settings } from "lucide-react";
import type { ReactNode } from "react";

export type ViewKey = "today" | "activities" | "trends" | "load" | "ai" | "settings";

type Props = {
  view: ViewKey;
  onViewChange: (view: ViewKey) => void;
  children: ReactNode;
};

const navItems: { key: ViewKey; label: string; icon: typeof CalendarDays }[] = [
  { key: "today", label: "Today", icon: CalendarDays },
  { key: "activities", label: "Activities", icon: Activity },
  { key: "trends", label: "Trends", icon: HeartPulse },
  { key: "load", label: "Load", icon: LineChart },
  { key: "ai", label: "AI", icon: Bot },
  { key: "settings", label: "Settings", icon: Settings }
];

export function AppShell({ view, onViewChange, children }: Props) {
  return (
    <div className="min-h-screen bg-surface text-ink">
      <header className="sticky top-0 z-20 border-b border-line/80 bg-surface/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 lg:px-6">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-pine">Garmin Insight</div>
            <h1 className="text-lg font-semibold sm:text-xl">Training intelligence console</h1>
          </div>
          <div className="hidden rounded-lg border border-line bg-panel/80 px-3 py-2 text-sm text-muted sm:block">
            Grounded by your database
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 pb-28 pt-4 sm:pb-8 lg:px-6 xl:pl-56">{children}</main>
      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-panel/95 backdrop-blur sm:hidden">
        <div className="grid grid-cols-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = view === item.key;
            return (
              <button
                key={item.key}
                className={`flex h-16 flex-col items-center justify-center gap-1 text-[11px] font-medium ${
                  active ? "text-pine" : "text-muted"
                }`}
                onClick={() => onViewChange(item.key)}
                title={item.label}
                type="button"
              >
                <Icon size={20} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
      <aside className="fixed left-4 top-28 hidden w-44 rounded-xl border border-line bg-panel/80 p-2 shadow-soft backdrop-blur xl:block">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = view === item.key;
          return (
            <button
              key={item.key}
              className={`mb-1 flex h-10 w-full items-center gap-2 rounded-md px-3 text-sm font-medium ${
                active ? "bg-pine text-surface shadow-glow" : "text-muted hover:bg-panel2 hover:text-ink"
              }`}
              onClick={() => onViewChange(item.key)}
              type="button"
            >
              <Icon size={18} aria-hidden="true" />
              {item.label}
            </button>
          );
        })}
      </aside>
    </div>
  );
}
