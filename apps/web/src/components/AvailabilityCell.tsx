import type { Segment } from "../lib/matrix";
import { OPERATING_MINUTES, minuteToFmt } from "../lib/matrix";

type Props = {
  day: Date;
  segments: Segment[];
  onSelect: () => void;
};

function durationLabel(minutes: number): string {
  const hours = minutes / 60;
  return Number.isInteger(hours) ? `${hours}h` : `${hours.toFixed(1)}h`;
}

function tooltipFor(day: Date, seg: Segment): string {
  const startMin = seg.startMinuteOfDay;
  const endMin = seg.endMinuteOfDay;
  const label = seg.kind === "free" ? "Free" : "Permitted";
  return `${label} ${minuteToFmt(day, startMin)} - ${minuteToFmt(day, endMin)} (${durationLabel(
    endMin - startMin,
  )})`;
}

export function AvailabilityCell({ day, segments, onSelect }: Props) {
  const dayStartMin = 7 * 60;
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onSelect();
      }}
      className="relative h-8 flex-1 cursor-pointer overflow-hidden rounded ring-1 ring-zinc-200"
    >
      {segments.length === 0 ? (
        <div
          title="No data."
          className="absolute inset-0 bg-zinc-200"
        />
      ) : (
        segments.map((seg, i) => {
          const widthPct =
            ((seg.endMinuteOfDay - seg.startMinuteOfDay) / OPERATING_MINUTES) * 100;
          const leftPct = ((seg.startMinuteOfDay - dayStartMin) / OPERATING_MINUTES) * 100;
          const cls =
            seg.kind === "free"
              ? "bg-emerald-400 hover:bg-emerald-500"
              : "bg-rose-500 hover:bg-rose-600";
          return (
            <div
              key={`${seg.kind}-${i}-${seg.startMinuteOfDay}`}
              title={tooltipFor(day, seg)}
              style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
              className={`absolute top-0 h-full transition-colors ${cls}`}
            />
          );
        })
      )}
    </div>
  );
}
