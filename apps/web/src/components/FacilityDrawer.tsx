import { useEffect, useMemo } from "react";
import { format, isSameDay, parseISO } from "date-fns";

import type { FacilityAvailability } from "../types";
import { enumerateDays, fmtHM } from "../lib/matrix";

type Props = {
  facility: FacilityAvailability | null;
  rangeStart: string;
  rangeEnd: string;
  onClose: () => void;
};

const BOROUGH_LABELS: Record<string, string> = {
  M: "Manhattan",
  X: "Bronx",
  B: "Brooklyn",
  Q: "Queens",
  R: "Staten Island",
  "?": "Unknown",
};

export function FacilityDrawer({ facility, rangeStart, rangeEnd, onClose }: Props) {
  useEffect(() => {
    if (!facility) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [facility, onClose]);

  const days = useMemo(() => enumerateDays(rangeStart, rangeEnd), [rangeStart, rangeEnd]);

  if (!facility) return null;

  const f = facility.facility;
  const boroughLabel = BOROUGH_LABELS[f.borough] ?? f.borough;
  const totalHours = Math.round((facility.total_free_minutes / 60) * 10) / 10;
  const permitCount = facility.permitted_slots.length;

  return (
    <>
      <div
        className="fixed inset-0 z-20 bg-black/30"
        onClick={onClose}
        aria-hidden="true"
      />
      <aside className="fixed inset-y-0 right-0 z-30 flex w-[28rem] max-w-full flex-col border-l border-zinc-200 bg-white shadow-xl">
        <header className="flex items-start justify-between gap-3 border-b border-zinc-200 p-6">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-zinc-900">{f.field_label}</h2>
              {facility.has_full_closure && (
                <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-700">
                  Closed
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-zinc-600">
              {f.park_id} · {boroughLabel}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded p-1 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900"
          >
            ✕
          </button>
        </header>

        <section className="grid grid-cols-2 gap-3 border-b border-zinc-200 px-6 py-4 text-sm">
          <Stat label="Total free hours" value={`${totalHours}`} />
          <Stat label="Permitted blocks" value={String(permitCount)} />
          <Stat label="Surface" value={f.surface_type ?? "—"} />
          <Stat label="Lights" value={f.is_lighted ? "Yes" : "No"} />
        </section>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <ul className="space-y-4">
            {days.map((day) => (
              <DayBlock
                key={day.toISOString()}
                day={day}
                facility={facility}
              />
            ))}
          </ul>
        </div>
      </aside>
    </>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="font-medium text-zinc-900">{value}</div>
    </div>
  );
}

type DayBlockProps = {
  day: Date;
  facility: FacilityAvailability;
};

function DayBlock({ day, facility }: DayBlockProps) {
  const dayLabel = `${format(day, "EEE")} ${format(day, "M/d")}`;
  const permits = facility.permitted_slots.filter((s) =>
    isSameDay(parseISO(s.start), day) || isSameDay(parseISO(s.end), day),
  );
  const frees = facility.free_slots.filter((s) =>
    isSameDay(parseISO(s.start), day) || isSameDay(parseISO(s.end), day),
  );

  if (permits.length === 0 && frees.length === 0) {
    return (
      <li>
        <div className="text-sm font-medium text-zinc-900">{dayLabel}</div>
        <div className="text-sm text-zinc-600">Free all day (7am-10pm).</div>
      </li>
    );
  }

  return (
    <li>
      <div className="text-sm font-medium text-zinc-900">{dayLabel}</div>
      <ul className="mt-1 space-y-1 text-sm">
        {permits.map((p, i) => (
          <li key={`p-${i}`} className="text-rose-700">
            Permitted {fmtHM(parseISO(p.start))} - {fmtHM(parseISO(p.end))}
          </li>
        ))}
        {frees.map((s, i) => (
          <li key={`f-${i}`} className="text-emerald-700">
            Free {fmtHM(parseISO(s.start))} - {fmtHM(parseISO(s.end))}
          </li>
        ))}
      </ul>
    </li>
  );
}
