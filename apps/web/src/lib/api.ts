import type { AvailabilityResponse, SportSummary } from "../types";

async function getJSON<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      if (body && typeof body === "object" && "detail" in body) {
        detail = ` - ${String(body.detail)}`;
      }
    } catch {
      // body wasn't JSON; ignore.
    }
    throw new Error(`Request failed: ${response.status} ${response.statusText}${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function listSports(): Promise<SportSummary[]> {
  return getJSON<SportSummary[]>("/api/sports");
}

export async function getAvailability(params: {
  sport: string;
  from: string;
  to: string;
  borough?: string;
  minSlotMinutes?: number;
}): Promise<AvailabilityResponse> {
  const qs = new URLSearchParams();
  qs.set("sport", params.sport);
  qs.set("from", params.from);
  qs.set("to", params.to);
  if (params.borough) qs.set("borough", params.borough);
  if (params.minSlotMinutes !== undefined) {
    qs.set("min_slot_minutes", String(params.minSlotMinutes));
  }
  return getJSON<AvailabilityResponse>(`/api/availability?${qs.toString()}`);
}
