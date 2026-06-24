/**
 * API client for CampaignPulse backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API ${res.status}: ${error}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Campaigns
export async function fetchCampaigns(params?: {
  page?: number;
  page_size?: number;
  platform?: string;
  status?: string;
  sort_by?: string;
  sort_order?: string;
}) {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.page_size) searchParams.set("page_size", String(params.page_size));
  if (params?.platform) searchParams.set("platform", params.platform);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params?.sort_order) searchParams.set("sort_order", params.sort_order);
  const qs = searchParams.toString();
  return request<import("./types").CampaignListResponse>(
    `/api/campaigns${qs ? `?${qs}` : ""}`
  );
}

export async function fetchCampaignSummary() {
  return request<import("./types").CampaignSummary>("/api/campaigns/summary");
}

export async function fetchCampaign(id: number) {
  return request<import("./types").Campaign>(`/api/campaigns/${id}`);
}

export async function triggerSync() {
  return request<{ sync_results: unknown[]; total_platforms_synced: number }>(
    "/api/campaigns/sync",
    { method: "POST" }
  );
}

// Creatives
export async function fetchCreatives(campaignId?: number) {
  const qs = campaignId ? `?campaign_id=${campaignId}` : "";
  return request<import("./types").Creative[]>(`/api/creatives${qs}`);
}

export async function analyzeCreatives(creativeIds: number[]) {
  return request<import("./types").CreativeAnalysisResult[]>(
    "/api/creatives/analyze",
    {
      method: "POST",
      body: JSON.stringify({ creative_ids: creativeIds }),
    }
  );
}

// Budget
export async function fetchBudgetRecommendations(totalBudget?: number) {
  const qs = totalBudget ? `?total_budget=${totalBudget}` : "";
  return request<import("./types").BudgetRecommendationResponse>(
    `/api/budget/recommendations${qs}`
  );
}

// Landing Pages
export async function fetchLandingPages(campaignId?: number) {
  const qs = campaignId ? `?campaign_id=${campaignId}` : "";
  return request<import("./types").LandingPage[]>(`/api/landing-pages${qs}`);
}

export async function fetchLandingPageSummary() {
  return request<import("./types").LandingPagePerformanceSummary>(
    "/api/landing-pages/summary/performance"
  );
}

// Insights
export async function fetchInsights(params?: {
  type?: string;
  severity?: string;
  is_read?: boolean;
  limit?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.type) searchParams.set("type", params.type);
  if (params?.severity) searchParams.set("severity", params.severity);
  if (params?.is_read !== undefined) searchParams.set("is_read", String(params.is_read));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  const qs = searchParams.toString();
  return request<import("./types").InsightListResponse>(
    `/api/insights${qs ? `?${qs}` : ""}`
  );
}

export async function scanForAnomalies() {
  return request<import("./types").Insight[]>(
    "/api/insights/scan",
    { method: "POST" }
  );
}

export async function markInsightRead(id: number) {
  return request<import("./types").Insight>(
    `/api/insights/${id}/read`,
    { method: "PUT" }
  );
}

// Ad Platforms
export async function fetchPlatforms() {
  return request<import("./types").AdPlatform[]>("/api/platforms");
}
