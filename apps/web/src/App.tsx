import { useEffect, useState } from "react";
import { formatDistanceToNow, parseISO } from "date-fns";

import { AvailabilityMatrix } from "./components/AvailabilityMatrix";
import { FacilityDrawer } from "./components/FacilityDrawer";
import { QueryBar } from "./components/QueryBar";
import { getAvailability, listSports } from "./lib/api";
import type {
  AvailabilityResponse,
  FacilityAvailability,
  PermitDensity,
  SportSummary,
} from "./types";

const HIGH_VOLUME_THRESHOLD = 800;

export default function App() {
  const [sports, setSports] = useState<SportSummary[]>([]);
  const [sportsError, setSportsError] = useState<string | null>(null);
  const [response, setResponse] = useState<AvailabilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchingSport, setSearchingSport] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<FacilityAvailability | null>(null);

  useEffect(() => {
    let cancelled = false;
    listSports()
      .then((list) => {
        if (!cancelled) setSports(list);
      })
      .catch((err: Error) => {
        if (!cancelled) setSportsError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSearch(params: {
    sport: string;
    from: string;
    to: string;
    borough: string;
  }) {
    setLoading(true);
    setSearchingSport(params.sport);
    setError(null);
    try {
      const result = await getAvailability({
        sport: params.sport,
        from: params.from,
        to: params.to,
        borough: params.borough || undefined,
      });
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

  const sportLookup = new Map(sports.map((s) => [s.code, s] as const));
  const searchingSummary = searchingSport ? sportLookup.get(searchingSport) : undefined;

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <main className="mx-auto max-w-7xl space-y-4 p-6">
        <header className="space-y-1">
          <h1 className="text-3xl font-semibold tracking-tight">Field Finder</h1>
          <p className="text-sm text-zinc-600">
            NYC Parks athletic field availability
          </p>
        </header>

        <QueryBar
          sports={sports}
          sportsError={sportsError}
          onSearch={handleSearch}
          loading={loading}
        />

        <ResultPanel
          response={response}
          loading={loading}
          error={error}
          searchingSport={searchingSummary}
          sportLookup={sportLookup}
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
  searchingSport: SportSummary | undefined;
  sportLookup: Map<string, SportSummary>;
  onSelectFacility: (f: FacilityAvailability) => void;
};

function ResultPanel({
  response,
  loading,
  error,
  searchingSport,
  sportLookup,
  onSelectFacility,
}: ResultPanelProps) {
  if (loading) {
    const isHighVolume =
      searchingSport !== undefined &&
      searchingSport.facility_count > HIGH_VOLUME_THRESHOLD;
    const message = isHighVolume
      ? `Searching... this may take up to 30 seconds the first time for ${searchingSport.label}.`
      : "Searching...";
    return <LoadingSkeleton message={message} />;
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
  const sportLabel = sportLookup.get(response.sport)?.label ?? response.sport;

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

      <DensityBanner density={response.permit_density} sportLabel={sportLabel} />

      <AvailabilityMatrix response={response} onSelectFacility={onSelectFacility} />

      <ResultFooter response={response} />
    </div>
  );
}

function LoadingSkeleton({ message }: { message: string }) {
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-zinc-200 bg-white p-4 text-sm text-zinc-600">
        {message}
      </div>
      <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="flex animate-pulse items-center gap-3 border-b border-zinc-100 px-3 py-3 last:border-b-0"
          >
            <div className="h-8 w-64 shrink-0 rounded bg-zinc-200" />
            <div className="h-8 flex-1 rounded bg-zinc-100" />
            <div className="h-4 w-12 shrink-0 rounded bg-zinc-200" />
          </div>
        ))}
      </div>
    </div>
  );
}

function DensityBanner({
  density,
  sportLabel,
}: {
  density: PermitDensity;
  sportLabel: string;
}) {
  if (density === "high") return null;
  const text =
    density === "low"
      ? `Few permits are issued for ${sportLabel} at NYC Parks. Most facilities below are unpermitted, which typically means first-come, first-served use is allowed during operating hours.`
      : `No issued permits found for ${sportLabel} in this date range. These courts may be drop-in or seasonal. Always check posted signage on-site.`;
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
      {text}
    </div>
  );
}

function ResultFooter({ response }: { response: AvailabilityResponse }) {
  let relativeViewed = "just now";
  try {
    relativeViewed = formatDistanceToNow(parseISO(response.generated_at), {
      addSuffix: true,
    });
  } catch {
    // generated_at missing or unparseable; keep fallback.
  }
  return (
    <p className="px-1 text-xs text-zinc-500">
      Showing {response.total_facilities} fields. Data refreshed daily by NYC
      Parks. Permits viewed: {relativeViewed}.
    </p>
  );
}
