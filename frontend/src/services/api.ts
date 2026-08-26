/** Thin typed API client. All calls hit the FastAPI backend via the Vite proxy. */

import type {
  ChatMessageOut,
  CropInfo,
  FarmerWithListings,
  JoinPoolResponse,
  NotificationItem,
  PriceRecord,
  RecommendationResponse,
  TruckInfo,
  MandiInfo,
} from "@/types";

const BASE = "/api";

export class ApiError extends Error {
  code: string;
  suggestions?: string[];

  constructor(code: string, message: string, suggestions?: string[]) {
    super(message);
    this.code = code;
    this.suggestions = suggestions;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(
      "NETWORK_ERROR",
      "We couldn't reach Unnati. Check your connection and try again.",
    );
  }

  if (!response.ok) {
    let payload: { error?: { code?: string; message?: string; suggestions?: string[] } } = {};
    try {
      payload = await response.json();
    } catch {
      /* non-JSON error */
    }
    const error = payload.error ?? {};
    // Map backend codes to farmer-friendly copy.
    const friendly = error.code
      ? error.message ?? "Something went wrong."
      : "Something went wrong. Please try again.";
    throw new ApiError(error.code ?? "INTERNAL_ERROR", friendly, error.suggestions);
  }
  return response.json() as Promise<T>;
}

export const api = {
  crops: () => request<CropInfo[]>("/crops"),

  createListing: (body: {
    crop: string;
    quantity_kg: number;
    latitude: number;
    longitude: number;
    harvested_at?: string | null;
    preferred_radius_km?: number | null;
  }) =>
    request<{ id: number }>("/listings", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  recommend: (listingId: number) =>
    request<RecommendationResponse>("/recommendations", {
      method: "POST",
      body: JSON.stringify({ listing_id: listingId }),
    }),

  latestRecommendation: (listingId: number) =>
    request<RecommendationResponse>(`/recommendations/latest/${listingId}`),

  joinPool: (poolId: number, listingId: number) =>
    request<JoinPoolResponse>(`/pools/${poolId}/join`, {
      method: "POST",
      body: JSON.stringify({ listing_id: listingId }),
    }),

  farmers: () => request<FarmerWithListings[]>("/farmers"),
  trucks: () => request<TruckInfo[]>("/trucks"),
  mandis: () => request<MandiInfo[]>("/mandis"),
  prices: () => request<PriceRecord[]>("/mandis/prices"),
  pricesHistory: (days = 7) =>
    request<PriceRecord[]>(`/mandis/prices/history?days=${days}`),
  notifications: (farmerId: number) =>
    request<NotificationItem[]>(`/notifications/${farmerId}`),

  chat: (sessionId: string, text: string) =>
    request<{ session_id: string; reply: ChatMessageOut }>("/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, text }),
    }),

  resetDemo: () => request<{ status: string }>("/demo/reset", { method: "POST" }),
};
