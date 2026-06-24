"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Globe } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchLandingPages, fetchLandingPageSummary } from "@/lib/api";
import type {
  LandingPage,
  LandingPagePerformanceSummary,
} from "@/lib/types";
import {
  formatCurrency,
  formatNumber,
  formatPercent,
  formatRoas,
  getPlatformLabel,
  sanitizeUrl,
} from "@/lib/utils";

export default function LandingPagesPage() {
  const [pages, setPages] = useState<LandingPage[]>([]);
  const [summary, setSummary] = useState<LandingPagePerformanceSummary | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchLandingPages(),
      fetchLandingPageSummary(),
    ])
      .then(([pagesData, summaryData]) => {
        setPages(pagesData);
        setSummary(summaryData);
      })
      .catch((err) => {
        console.error("Failed to load landing pages:", err);
        setError(err instanceof Error ? err.message : "Failed to load data");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  if (error) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <Button
            className="mt-4"
            variant="outline"
            onClick={() => load()}
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          Landing Page Performance
        </h2>
        <p className="text-sm text-gray-500">
          Track how ad spend converts on your landing pages
        </p>
      </div>

      {/* Summary KPIs */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500">Total Visits</p>
              <p className="text-xl font-bold text-gray-900">
                {formatNumber(summary.total_visits)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500">Total Conversions</p>
              <p className="text-xl font-bold text-green-600">
                {formatNumber(summary.total_conversions)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500">Conversion Rate</p>
              <p className="text-xl font-bold text-blue-600">
                {formatPercent(summary.overall_conversion_rate)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-gray-500">Overall ROAS</p>
              <p className="text-xl font-bold text-amber-600">
                {formatRoas(summary.overall_roas)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {summary?.top_performing_url && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Top Performer</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-green-500" />
              <a
                href={sanitizeUrl(summary.top_performing_url)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-blue-600 hover:underline"
              >
                {summary.top_performing_url}
              </a>
              <ExternalLink className="h-3 w-3 text-gray-400" />
            </div>
            {summary.top_conversion_rate !== null && (
              <p className="mt-1 text-sm text-gray-500">
                Conversion rate: {formatPercent(summary.top_conversion_rate)}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Landing pages table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">All Landing Pages</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {pages.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-sm text-gray-500">
              No landing pages tracked yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left font-medium text-gray-500">
                      URL
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">
                      Platform
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">
                      Visits
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">
                      Conversions
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">
                      Conv. Rate
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">
                      Revenue
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">
                      Cost
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">
                      ROAS
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">
                      Bounce Rate
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {pages.map((lp) => (
                    <tr
                      key={lp.id}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="max-w-xs truncate px-4 py-3 font-medium text-gray-900">
                        <div className="flex items-center gap-2">
                          <Globe className="h-4 w-4 shrink-0 text-gray-400" />
                          <span className="truncate">{lp.url}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">
                          {getPlatformLabel(lp.platform)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {formatNumber(lp.visits)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {formatNumber(lp.conversions)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm font-medium">
                        {lp.conversion_rate !== null
                          ? formatPercent(lp.conversion_rate)
                          : "-"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {formatCurrency(lp.revenue)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {formatCurrency(lp.cost)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm font-medium">
                        {formatRoas(lp.roas)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {lp.bounce_rate !== null
                          ? formatPercent(lp.bounce_rate * 100)
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
