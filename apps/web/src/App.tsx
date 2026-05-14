import { useState } from "react";

import { AvailabilityMatrix } from "./components/AvailabilityMatrix";
import { FacilityDrawer } from "./components/FacilityDrawer";
import { QueryBar } from "./components/QueryBar";
import { getAvailability } from "./lib/api";
import type { AvailabilityResponse, FacilityAvailability } from "./types";

export default function App() {
  const [response, setResponse] = useState<AvailabilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<FacilityAvailability | null>(null);

  async function handleSearch(params: { sport: string; from: string; to: string }) {
    setLoading(true);
    setError(null);
    try {
      const result = await getAvailability(params);
      setResponse(result);
      setSelected(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <main className="mx-auto max-w-7xl space-y-4 p-6">
        <header className="space-y-1">
          <h1 className="text-3xl font-semibold tracking-tight">Field Finder</h1>
          <p className="text-sm text-zinc-600">
            NYC Parks athletic field availability
          </p>
        </header>

        <QueryBar onSearch={handleSearch} loading={loading} />

        <ResultPanel
          response={response}
          loading={loading}
          error={error}
          onSelectFacility={setSelected}
        />
      </main>

      <FacilityDrawer
        facility={selected}
        rangeStart={response?.range_start ?? ""}
        rangeEnd={response?.range_end ?? ""}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}

type ResultPanelProps = {
  response: AvailabilityResponse | null;
  loading: boolean;
  error: string | null;
  onSelectFacility: (f: FacilityAvailability) => void;
};

function ResultPanel({ response, loading, error, onSelectFacility }: ResultPanelProps) {
  if (loading) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-6 text-sm text-zinc-600">
        Searching...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!response) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-zinc-100 p-6 text-sm text-zinc-600">
        Pick a sport and date range to begin.
      </div>
    );
  }

  const totalHours = Math.round(response.total_free_minutes / 60);
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
        <p className="text-sm text-zinc-900">
          <span className="font-semibold">{response.facilities.length}</span> fields
          matched,{" "}
          <span className="font-semibold">{totalHours}</span> total free hours,
          data source:{" "}
          <span className="font-mono text-xs">{response.cache_status}</span>
        </p>
        <div className="mt-2 flex items-center gap-4 text-xs text-zinc-600">
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block h-3 w-3 rounded bg-emerald-400" />
            Available
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block h-3 w-3 rounded bg-rose-500" />
            Permitted (busy)
          </span>
        </div>
      </div>
      <AvailabilityMatrix response={response} onSelectFacility={onSelectFacility} />
    </div>
  );
}
