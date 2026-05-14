import {
  eachDayOfInterval,
  format,
  isSameDay,
  parseISO,
  subDays,
} from "date-fns";

import type { FacilityAvailability, TimeWindow } from "../types";

export const OPERATING_START_HOUR = 7;
export const OPERATING_END_HOUR = 22;
export const OPERATING_MINUTES = (OPERATING_END_HOUR - OPERATING_START_HOUR) * 60;
const DAY_START_MIN = OPERATING_START_HOUR * 60;
const DAY_END_MIN = OPERATING_END_HOUR * 60;

export type Segment = {
  kind: "free" | "busy";
  startMinuteOfDay: number;
  endMinuteOfDay: number;
  startISO: string;
  endISO: string;
};

export type DaySegments = {
  date: Date;
  segments: Segment[];
};

export function enumerateDays(startISO: string, endISO: string): Date[] {
  const start = parseISO(startISO);
  const end = parseISO(endISO);
  const lastDay = subDays(end, 1);
  if (lastDay < start) return [];
  return eachDayOfInterval({ start, end: lastDay });
}

function minuteOfDay(date: Date): number {
  return date.getHours() * 60 + date.getMinutes();
}

function isoForMinute(day: Date, minute: number): string {
  const d = new Date(day);
  d.setHours(0, 0, 0, 0);
  d.setMinutes(minute);
  return format(d, "yyyy-MM-dd'T'HH:mm:ss");
}

function clipSegments(
  slots: TimeWindow[],
  day: Date,
  kind: "free" | "busy",
): Segment[] {
  const out: Segment[] = [];
  for (const slot of slots) {
    const start = parseISO(slot.start);
    const end = parseISO(slot.end);
    if (!isSameDay(start, day) && !isSameDay(end, day)) continue;
    const startMin = isSameDay(start, day) ? minuteOfDay(start) : DAY_START_MIN;
    const endMin = isSameDay(end, day) ? minuteOfDay(end) : DAY_END_MIN;
    const clippedStart = Math.max(startMin, DAY_START_MIN);
    const clippedEnd = Math.min(endMin, DAY_END_MIN);
    if (clippedStart < clippedEnd) {
      out.push({
        kind,
        startMinuteOfDay: clippedStart,
        endMinuteOfDay: clippedEnd,
        startISO: slot.start,
        endISO: slot.end,
      });
    }
  }
  return out;
}

export function buildDaySegments(
  facility: FacilityAvailability,
  day: Date,
): DaySegments {
  const raw: Segment[] = [
    ...clipSegments(facility.free_slots, day, "free"),
    ...clipSegments(facility.permitted_slots, day, "busy"),
  ].sort((a, b) => a.startMinuteOfDay - b.startMinuteOfDay);

  // Fill any uncovered gaps inside the operating window with "free".
  const segments: Segment[] = [];
  let cursor = DAY_START_MIN;
  for (const seg of raw) {
    if (seg.startMinuteOfDay > cursor) {
      segments.push({
        kind: "free",
        startMinuteOfDay: cursor,
        endMinuteOfDay: seg.startMinuteOfDay,
        startISO: isoForMinute(day, cursor),
        endISO: isoForMinute(day, seg.startMinuteOfDay),
      });
    }
    if (seg.endMinuteOfDay > cursor) {
      segments.push({
        ...seg,
        startMinuteOfDay: Math.max(seg.startMinuteOfDay, cursor),
      });
      cursor = seg.endMinuteOfDay;
    }
  }
  if (cursor < DAY_END_MIN) {
    segments.push({
      kind: "free",
      startMinuteOfDay: cursor,
      endMinuteOfDay: DAY_END_MIN,
      startISO: isoForMinute(day, cursor),
      endISO: isoForMinute(day, DAY_END_MIN),
    });
  }

  return { date: day, segments };
}

export function totalFreeHours(f: FacilityAvailability): number {
  return Math.round((f.total_free_minutes / 60) * 10) / 10;
}

export function fmtHM(date: Date): string {
  return format(date, "h:mm a");
}

export function minuteToFmt(day: Date, minute: number): string {
  const d = new Date(day);
  d.setHours(0, 0, 0, 0);
  d.setMinutes(minute);
  return fmtHM(d);
}
