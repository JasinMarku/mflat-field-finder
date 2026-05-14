import { useMemo, useState } from "react";

import type { AvailabilityResponse, FacilityAvailability } from "../types";
import { enumerateDays } from "../lib/matrix";
import { FieldRow } from "./FieldRow";
import { MatrixHeader } from "./MatrixHeader";

const MAX_DAYS = 14;
const INITIAL_ROWS = 100;

type Props = {
  response: AvailabilityResponse;
  onSelectFacility: (f: FacilityAvailability) => void;
};

export function AvailabilityMatrix({ response, onSelectFacility }: Props) {
  const [showAll, setShowAll] = useState(false);

  const allDays = useMemo(
    () => enumerateDays(response.range_start, response.range_end),
    [response.range_start, response.range_end],
  );
  const days = allDays.slice(0, MAX_DAYS);
  const dayLimitHit = allDays.length > MAX_DAYS;

  const facilities = useMemo(
    () =>
      [...response.facilities].sort(
        (a, b) => b.total_free_minutes - a.total_free_minutes,
      ),
    [response.facilities],
  );

  if (facilities.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-6 text-sm text-zinc-600">
        No fields match this query.
      </div>
    );
  }

  const limited = !showAll && facilities.length > INITIAL_ROWS;
  const visible = limited ? facilities.slice(0, INITIAL_ROWS) : facilities;

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
      {dayLimitHit && (
        <p className="border-b border-zinc-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          Showing first {MAX_DAYS} days.
        </p>
      )}
      <div className="max-h-[70vh] overflow-y-auto">
        <MatrixHeader days={days} />
        {visible.map((facility) => (
          <FieldRow
            key={facility.facility.facility_id}
            facility={facility}
            days={days}
            onSelect={() => onSelectFacility(facility)}
          />
        ))}
        {limited && (
          <div className="flex items-center justify-between gap-3 border-t border-zinc-100 bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
            <span>
              Showing {INITIAL_ROWS} of {facilities.length}.
            </span>
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100"
            >
              Load more
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
