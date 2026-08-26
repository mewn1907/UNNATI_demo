/** Mirrors the FastAPI response schemas. */

export interface PoolMemberInfo {
  farmer_name: string;
  village: string;
  quantity_kg: number;
  distance_km: number;
}

export interface PoolInfo {
  farmer_count: number;
  total_quantity_kg: number;
  remaining_capacity_kg: number;
  utilization_percent: number;
  members: PoolMemberInfo[];
}

export interface OptionEconomics {
  mandi_id: number | null;
  mandi_name: string;
  price_per_kg: number;
  distance_km: number;
  gross_revenue: number;
  transport_cost: number;
  spoilage_loss: number;
  spoilage_percentage: number;
  net_profit: number;
}

export interface CandidateOption extends OptionEconomics {
  candidate_id: string;
  truck_id: string | null;
  truck_registration: string | null;
  is_return_trip: boolean;
  departure_at: string | null;
  pool: PoolInfo | null;
  score: number;
  valid: boolean;
  rejection_reason?: string | null;
}

export interface SpoilageInfo {
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  hours_remaining: number;
  estimated_loss_percentage: number;
  temperature_c: number;
  humidity_pct: number;
  crop_age_hours: number;
}

export interface LLMExplanation {
  headline: string;
  summary: string;
  why_this_option: string[];
  action: string;
  urgency: string;
  warnings: string[];
}

export interface RecommendationResponse {
  recommendation_id: string;
  listing_id: number;
  crop_name: string;
  quantity_kg: number;
  pool_id: number | null;
  baseline: OptionEconomics;
  recommended: CandidateOption;
  alternatives: CandidateOption[];
  net_gain: number;
  spoilage: SpoilageInfo;
  score: number;
  explanation: LLMExplanation;
  llm_powered: boolean;
  data_labels: Record<string, string>;
  map_points: {
    farmer: MapPoint;
    truck_origin: MapPoint;
    recommended_mandi: MapPoint;
    alternative_mandis: MapPoint[];
    pool_members: MapPoint[];
  };
  calculation_ms: number;
}

export interface MapPoint {
  name: string;
  latitude: number;
  longitude: number;
}

export interface JoinPoolResponse {
  status: string;
  message: string;
  pool_id: number;
  truck_id: string;
  destination_mandi: string;
  departure_at: string;
  quantity_kg: number;
}

export interface CropInfo {
  id: number;
  name: string;
  category: string;
  unit: string;
  baseline_shelf_life_hours: number;
}

export interface FarmerWithListings {
  id: number;
  name: string;
  village: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  listings: { id: number; crop: string; quantity_kg: number; harvested_at: string; status: string }[];
}

export interface TruckRouteInfo {
  route_id: string;
  origin_name: string;
  origin_latitude: number;
  origin_longitude: number;
  destination_mandi_id: number | null;
  destination_mandi: string | null;
  departure_at: string;
  estimated_arrival_at: string;
  return_available: boolean;
  return_destination_region: string;
  distance_km: number;
}

export interface TruckInfo {
  id: string;
  registration_number: string;
  capacity_kg: number;
  available_capacity_kg: number;
  status: string;
  current_latitude: number;
  current_longitude: number;
  routes: TruckRouteInfo[];
}

export interface MandiInfo {
  id: number;
  name: string;
  city: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
}

export interface PriceRecord {
  mandi_id: number;
  mandi: string;
  crop: string;
  price_per_kg: number;
  price_per_quintal: number;
  recorded_at: string;
  source: string;
  label: string;
}

export interface NotificationItem {
  id: number;
  type: string;
  title: string;
  message: string;
  status: string;
  created_at: string;
}

export interface QuickReply {
  label: string;
  value: string;
}

export interface ChatMessageOut {
  role: "bot";
  text: string;
  quick_replies: QuickReply[];
  recommendation_id: string | null;
  joined: boolean;
}
