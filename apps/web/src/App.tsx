import { useState } from "react";

import { QueryBar } from "./components/QueryBar";
import { getAvailability } from "./lib/api";
import type { AvailabilityResponse } from "./types";

export default function App() {
  const [response, setResponse] = useState<AvailabilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(params: { sport: string; from: string; to: string }) {
    setLoading(true);
    setError(null);
    try {
      const result = await getAvailability(params);
      setResponse(result);
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
      <main className="mx-auto max-w-6xl space-y-6 p-6">
        <header className="space-y-1">
          <h1 className="text-3xl font-semibold tracking-tight">Field Finder</h1>
          <p className="text-sm text-zinc-600">
            NYC Parks athletic field availability
          </p>
        </header>

        <QueryBar onSearch={handleSearch} loading={loading} />

        <ResultPanel response={response} loading={loading} error={error} />
      </main>
    </div>
  );
}

type ResultPanelProps = {
  response: AvailabilityResponse | null;
  loading: boolean;
  error: string | null;
};

function ResultPanel({ response, loading, error }: ResultPanelProps) {
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
    <div className="space-y-3 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
      <p className="text-base text-zinc-900">
        <span className="font-semibold">{response.facilities.length}</span> fields
        matched,{" "}
        <span className="font-semibold">{totalHours}</span> total free hours,
        data source:{" "}
        <span className="font-mono text-sm">{response.cache_status}</span>
      </p>
      <p className="text-sm text-zinc-500">Calendar view coming in next phase.</p>
    </div>
  );
}
