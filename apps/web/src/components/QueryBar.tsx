import { useEffect, useState } from "react";
import { format, addDays } from "date-fns";

import { listSports } from "../lib/api";
import type { SportSummary } from "../types";

type Params = { sport: string; from: string; to: string };

type Props = {
  onSearch: (params: Params) => void;
  loading: boolean;
};

const today = () => format(new Date(), "yyyy-MM-dd");
const inAWeek = () => format(addDays(new Date(), 7), "yyyy-MM-dd");

export function QueryBar({ onSearch, loading }: Props) {
  const [sports, setSports] = useState<SportSummary[]>([]);
  const [sportsError, setSportsError] = useState<string | null>(null);
  const [sport, setSport] = useState<string>("soccer");
  const [from, setFrom] = useState<string>(today());
  const [to, setTo] = useState<string>(inAWeek());

  useEffect(() => {
    let cancelled = false;
    listSports()
      .then((list) => {
        if (cancelled) return;
        setSports(list);
        if (!list.some((s) => s.code === "soccer") && list.length > 0) {
          setSport(list[0].code);
        }
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setSportsError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const invalidRange = from >= to;
  const disabled = loading || invalidRange || !sport;

  return (
    <div className="flex flex-wrap items-end gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
      <label className="flex flex-col text-sm text-zinc-700">
        <span className="mb-1 font-medium">Sport</span>
        <select
          value={sport}
          onChange={(e) => setSport(e.target.value)}
          className="min-w-[10rem] rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-zinc-400"
        >
          {sports.length === 0 && (
            <option value="soccer">soccer</option>
          )}
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

      <button
        type="button"
        disabled={disabled}
        onClick={() => onSearch({ sport, from, to })}
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-400 disabled:cursor-not-allowed disabled:bg-zinc-400"
      >
        {loading ? "Searching..." : "Search"}
      </button>

      {sportsError && (
        <p className="w-full text-sm text-red-600">
          Could not load sport list: {sportsError}
        </p>
      )}
      {invalidRange && (
        <p className="w-full text-sm text-amber-600">
          "From" must be earlier than "To".
        </p>
      )}
    </div>
  );
}
