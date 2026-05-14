const BOROUGH_LABELS: Record<string, string> = {
  M: "Manhattan",
  X: "Bronx",
  B: "Brooklyn",
  Q: "Queens",
  R: "Staten Island",
};

export function boroughLabel(code: string): string {
  return BOROUGH_LABELS[code] ?? code;
}

const FIELD_PREFIX_TO_FULL: Record<string, string> = {
  Pkb: "Pickleball Court",
  Scr: "Soccer Field",
  Ftb: "Football Field",
  Bsb: "Baseball Field",
  Sof: "Softball Field",
  Vol: "Volleyball Court",
  Hbl: "Handball Court",
  Ten: "Tennis Court",
  Crk: "Cricket Field",
  Lax: "Lacrosse Field",
  Bbl: "Basketball Court",
};

export function expandFieldLabel(label: string): string {
  const m = label.match(/^([A-Za-z]+)\s+(.+)$/);
  if (m && FIELD_PREFIX_TO_FULL[m[1]]) {
    return `${FIELD_PREFIX_TO_FULL[m[1]]} ${m[2]}`;
  }
  return label;
}
