export type SportSummary = {
  code: string;
  label: string;
  facility_count: number;
};

export type TimeWindow = {
  start: string;
  end: string;
};

export type Facility = {
  facility_id: string;
  park_id: string;
  borough: string;
  field_label: string;
  sports: string[];
  surface_type: string | null;
  is_lighted: boolean;
  is_active: boolean;
};

export type FacilityAvailability = {
  facility: Facility;
  free_slots: TimeWindow[];
  permitted_slots: TimeWindow[];
  total_free_minutes: number;
  has_full_closure: boolean;
};

export type AvailabilityResponse = {
  sport: string;
  range_start: string;
  range_end: string;
  facilities: FacilityAvailability[];
  total_facilities: number;
  total_free_minutes: number;
  generated_at: string;
  cache_status: string;
};
