/** CampaignPulse TypeScript type definitions */

export interface Campaign {
  id: number;
  name: string;
  platform: "google" | "meta" | "taboola" | "tiktok";
  platform_campaign_id: string | null;
  status: "active" | "paused" | "completed" | "archived";
  daily_budget: number | null;
  total_budget: number | null;
  spent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  cpa: number | null;
  roas: number | null;
  revenue: number;
  ctr: number | null;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignListResponse {
  items: Campaign[];
  total: number;
  page: number;
  page_size: number;
}

export interface CampaignSummary {
  total_campaigns: number;
  active_campaigns: number;
  total_impressions: number;
  total_clicks: number;
  total_conversions: number;
  total_spent: number;
  total_revenue: number;
  overall_roas: number;
  overall_ctr: number;
  overall_cpa: number;
  by_platform: Record<string, PlatformBreakdown>;
}

export interface PlatformBreakdown {
  count: number;
  impressions: number;
  clicks: number;
  conversions: number;
  spent: number;
  revenue: number;
}

export interface Creative {
  id: number;
  campaign_id: number;
  platform: string;
  platform_creative_id: string | null;
  headline: string;
  body: string | null;
  image_url: string | null;
  cta: string | null;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  cpa: number | null;
  roas: number | null;
  ctr: number | null;
  ai_score: number | null;
  ai_analysis: string | null;
  created_at: string;
}

export interface CreativeAnalysisRequest {
  creative_ids: number[];
  include_recommendations?: boolean;
}

export interface CreativeAnalysisResult {
  creative_id: number;
  headline: string;
  ai_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  predicted_ctr: number | null;
  predicted_conversion_rate: number | null;
}

export interface BudgetAllocation {
  campaign_id: number;
  campaign_name: string;
  platform: string;
  current_budget: number;
  recommended_budget: number;
  change_amount: number;
  change_percent: number;
  rationale: string;
  expected_impact: string;
  confidence: number;
}

export interface BudgetRecommendationResponse {
  recommendations: BudgetAllocation[];
  total_current_budget: number;
  total_recommended_budget: number;
  expected_roas_improvement: number | null;
  estimated_additional_revenue: number | null;
  summary: string;
}

export interface LandingPage {
  id: number;
  campaign_id: number;
  platform: string;
  url: string;
  visits: number;
  unique_visits: number;
  conversions: number;
  conversion_rate: number | null;
  revenue: number;
  cost: number;
  roas: number | null;
  bounce_rate: number | null;
  avg_time_on_page: number | null;
  created_at: string;
  updated_at: string;
}

export interface LandingPagePerformanceSummary {
  total_visits: number;
  total_conversions: number;
  overall_conversion_rate: number;
  total_revenue: number;
  total_cost: number;
  overall_roas: number;
  top_performing_url: string | null;
  top_conversion_rate: number | null;
}

export interface Insight {
  id: number;
  type: "anomaly" | "recommendation" | "insight" | "alert";
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  platform: string | null;
  campaign_id: number | null;
  campaign_name: string | null;
  metric_name: string | null;
  current_value: number | null;
  previous_value: number | null;
  threshold: number | null;
  is_read: boolean;
  created_at: string;
}

export interface InsightListResponse {
  items: Insight[];
  total: number;
  unread_count: number;
}

export interface AdPlatform {
  id: number;
  name: string;
  platform_type: string;
  is_connected: boolean;
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
}
