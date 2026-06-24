"use client";

import { useEffect, useState } from "react";
import {
  Eye,
  DollarSign,
  MousePointerClick,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PlatformBreakdownCard } from "@/components/dashboard/platform-breakdown";
import { RecentInsights } from "@/components/dashboard/recent-insights";
import { PerformanceChart } from "@/components/dashboard/performance-chart";
import { fetchCampaignSummary, fetchInsights } from "@/lib/api";
import type { CampaignSummary, Insight } from "@/lib/types";
import {
  formatCompactNumber,
  formatCurrency,
  formatRoas,
} from "@/lib/utils";

export default function DashboardPage() {
  const [summary, setSummary] = useState<CampaignSummary | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [summaryData, insightsData] = await Promise.all([
          fetchCampaignSummary(),
          fetchInsights({ limit: 5 }),
        ]);
        setSummary(summaryData);
        setInsights(insightsData.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="mt-4 text-sm text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <Button
            className="mt-4"
            variant="outline"
            onClick={() => window.location.reload()}
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!summary) return null;

  const kpis = [
    {
      title: "Total Impressions",
      value: formatCompactNumber(summary.total_impressions),
      icon: Eye,
      change: "+12.3%",
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      title: "Total Spend",
      value: formatCurrency(summary.total_spent),
      icon: DollarSign,
      change: "+8.1%",
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      title: "Conversions",
      value: formatCompactNumber(summary.total_conversions),
      icon: Target,
      change: "+15.2%",
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
    {
      title: "Overall ROAS",
      value: formatRoas(summary.overall_roas),
      icon: TrendingUp,
      change: "+5.4%",
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
    {
      title: "Avg CPA",
      value: formatCurrency(summary.overall_cpa),
      icon: Users,
      change: "-3.2%",
      color: "text-rose-600",
      bg: "bg-rose-50",
    },
    {
      title: "CTR",
      value: `${summary.overall_ctr.toFixed(2)}%`,
      icon: MousePointerClick,
      change: "+0.8%",
      color: "text-cyan-600",
      bg: "bg-cyan-50",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-sm text-gray-500">
            {summary.total_campaigns} campaigns across{" "}
            {Object.keys(summary.by_platform).length} platforms
          </p>
        </div>
        <Badge variant="success" className="text-xs">
          {summary.active_campaigns} Active Campaigns
        </Badge>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <Card key={kpi.title}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className={`rounded-lg ${kpi.bg} p-2 ${kpi.color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs text-gray-500">
                      {kpi.title}
                    </p>
                    <p className="text-lg font-bold text-gray-900">
                      {kpi.value}
                    </p>
                  </div>
                </div>
                <p className={`mt-1 text-xs ${kpi.color}`}>
                  {kpi.change} vs last period
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Performance Chart */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Revenue & Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <PerformanceChart summary={summary} />
            </CardContent>
          </Card>
        </div>

        {/* Recent Insights */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <RecentInsights insights={insights} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Platform Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Platform Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Object.entries(summary.by_platform).map(
              ([platform, data]) => (
                <PlatformBreakdownCard
                  key={platform}
                  platform={platform}
                  data={data}
                />
              )
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
