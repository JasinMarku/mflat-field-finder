import type { FacilityAvailability } from "../types";
import { buildDaySegments, totalFreeHours } from "../lib/matrix";
import { boroughLabel, expandFieldLabel } from "../lib/labels";
import { AvailabilityCell } from "./AvailabilityCell";

type Props = {
  facility: FacilityAvailability;
  days: Date[];
  onSelect: () => void;
};

export function FieldRow({ facility, days, onSelect }: Props) {
  return (
    <div
      onClick={onSelect}
      className="flex cursor-pointer items-center gap-1 border-b border-zinc-100 px-3 py-2 hover:bg-zinc-50"
    >
      <div className="w-64 shrink-0 overflow-hidden">
        <div className="flex items-center gap-2">
          <div className="truncate text-sm font-medium text-zinc-900">
            {expandFieldLabel(facility.facility.field_label)}
          </div>
          {facility.has_full_closure && (
            <span className="shrink-0 rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-700">
              Closed
            </span>
          )}
        </div>
        <div className="truncate text-xs text-zinc-500">
          {facility.facility.park_id} · {boroughLabel(facility.facility.borough)}
        </div>
      </div>

      <div className="flex flex-1 gap-1">
        {days.map((day) => {
          const { segments } = buildDaySegments(facility, day);
          return (
            <AvailabilityCell
              key={day.toISOString()}
              day={day}
              segments={segments}
              onSelect={onSelect}
            />
          );
        })}
      </div>

      <div className="w-20 shrink-0 text-right text-sm font-semibold tabular-nums text-zinc-900">
        {totalFreeHours(facility)} h
      </div>
    </div>
  );
}
