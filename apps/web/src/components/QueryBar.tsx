import { useEffect, useState } from "react";
import { format, addDays, differenceInCalendarDays, parseISO } from "date-fns";

import type { SportSummary } from "../types";

type Params = {
  sport: string;
  from: string;
  to: string;
  borough: string;
};

type Props = {
  sports: SportSummary[];
  sportsError: string | null;
  onSearch: (params: Params) => void;
  loading: boolean;
};

const today = () => format(new Date(), "yyyy-MM-dd");
const inAWeek = () => format(addDays(new Date(), 7), "yyyy-MM-dd");

const BOROUGH_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "All boroughs" },
  { value: "M", label: "Manhattan" },
  { value: "B", label: "Brooklyn" },
  { value: "Q", label: "Queens" },
  { value: "X", label: "Bronx" },
  { value: "R", label: "Staten Island" },
];

const MAX_RANGE_DAYS = 31;

export function QueryBar({ sports, sportsError, onSearch, loading }: Props) {
  const [sport, setSport] = useState<string>("soccer");
  const [from, setFrom] = useState<string>(today());
  const [to, setTo] = useState<string>(inAWeek());
  const [borough, setBorough] = useState<string>("");

  useEffect(() => {
    if (sports.length === 0) return;
    if (!sports.some((s) => s.code === sport)) {
      const preferred = sports.find((s) => s.code === "soccer");
      setSport((preferred ?? sports[0]).code);
    }
  }, [sports, sport]);

  const invalidOrder = from >= to;
  const rangeDays =
    invalidOrder || !from || !to
      ? 0
      : differenceInCalendarDays(parseISO(to), parseISO(from));
  const rangeTooLong = rangeDays > MAX_RANGE_DAYS;
  const disabled = loading || invalidOrder || rangeTooLong || !sport;

  return (
    <div className="flex flex-wrap items-end gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
      <label className="flex flex-col text-sm text-zinc-700">
        <span className="mb-1 font-medium">Sport</span>
        <select
          value={sport}
          onChange={(e) => setSport(e.target.value)}
          className="min-w-[10rem] rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        >
          {sports.length === 0 && <option value="soccer">soccer</option>}
          {sports.map((s) => (
            <option key={s.code} value={s.code}>
              {s.label} ({s.facility_count})
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col text-sm text-zinc-700">
        <span className="mb-1 font-medium">From</span>
        <input
          type="date"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
          className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </label>

      <label className="flex flex-col text-sm text-zinc-700">
        <span className="mb-1 font-medium">To</span>
        <input
          type="date"
          value={to}
          onChange={(e) => setTo(e.target.value)}
          className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        />
      </label>

      <label className="flex flex-col text-sm text-zinc-700">
        <span className="mb-1 font-medium">Borough</span>
        <select
          value={borough}
          onChange={(e) => setBorough(e.target.value)}
          className="min-w-[10rem] rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        >
          {BOROUGH_OPTIONS.map((opt) => (
            <option key={opt.value || "all"} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>

      <button
        type="button"
        disabled={disabled}
        onClick={() => onSearch({ sport, from, to, borough })}
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-400 disabled:cursor-not-allowed disabled:bg-zinc-400"
      >
        {loading ? "Searching..." : "Search"}
      </button>

      {sportsError && (
        <p className="w-full text-sm text-red-600">
          Could not load sport list: {sportsError}
        </p>
      )}
      {invalidOrder && (
        <p className="w-full text-xs text-red-600">From must be before To.</p>
      )}
      {!invalidOrder && rangeTooLong && (
        <p className="w-full text-xs text-red-600">
          Range limited to {MAX_RANGE_DAYS} days max.
        </p>
      )}
    </div>
  );
}
