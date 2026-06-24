"use client";

import { useEffect, useState } from "react";
import { ArrowUpCircle, ArrowDownCircle, DollarSign } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchBudgetRecommendations } from "@/lib/api";
import type { BudgetRecommendationResponse } from "@/lib/types";
import { formatCurrency, getPlatformLabel } from "@/lib/utils";

export default function BudgetPage() {
  const [data, setData] = useState<BudgetRecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchBudgetRecommendations();
        setData(result);
      } catch (err) {
        console.error("Failed to load budget recommendations:", err);
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Budget Optimizer</h2>
        <p className="text-sm text-gray-500">
          AI-driven budget allocation recommendations across campaigns
        </p>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : error ? (
        <div className="flex h-64 items-center justify-center">
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
      ) : !data || data.recommendations.length === 0 ? (
        <Card>
          <CardContent className="flex h-64 items-center justify-center">
            <div className="text-center">
              <DollarSign className="mx-auto h-8 w-8 text-gray-400" />
              <p className="mt-2 text-sm text-gray-500">
                {data?.summary || "No active campaigns to optimize."}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Summary */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-gray-500">Total Budget</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatCurrency(data.total_current_budget)}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-gray-500">Expected ROAS Improvement</p>
                <p className="text-xl font-bold text-green-600">
                  {data.expected_roas_improvement !== null
                    ? `+${(data.expected_roas_improvement * 100).toFixed(1)}%`
                    : "N/A"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-gray-500">
                  Est. Additional Revenue
                </p>
                <p className="text-xl font-bold text-blue-600">
                  {data.estimated_additional_revenue !== null
                    ? formatCurrency(data.estimated_additional_revenue)
                    : "N/A"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-xs text-gray-500">Campaigns Optimized</p>
                <p className="text-xl font-bold text-gray-900">
                  {data.recommendations.length}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Summary text */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Executive Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-700">{data.summary}</p>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Allocation Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-gray-100">
                {data.recommendations.map((rec) => (
                  <div key={rec.campaign_id} className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-900">
                            {rec.campaign_name}
                          </h3>
                          <Badge variant="outline">
                            {getPlatformLabel(rec.platform)}
                          </Badge>
                        </div>
                        <p className="mt-2 text-sm text-gray-600">
                          {rec.rationale}
                        </p>
                        <p className="mt-1 text-sm text-blue-600">
                          {rec.expected_impact}
                        </p>
                      </div>
                      <div className="ml-6 shrink-0 text-right">
                        <div className="flex items-center gap-2">
                          {rec.change_amount > 0 ? (
                            <ArrowUpCircle className="h-5 w-5 text-green-500" />
                          ) : rec.change_amount < 0 ? (
                            <ArrowDownCircle className="h-5 w-5 text-red-500" />
                          ) : null}
                          <span
                            className={`text-lg font-bold ${
                              rec.change_amount > 0
                                ? "text-green-600"
                                : rec.change_amount < 0
                                  ? "text-red-600"
                                  : "text-gray-600"
                            }`}
                          >
                            {rec.change_amount > 0 ? "+" : ""}
                            {formatCurrency(rec.change_amount)}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center justify-end gap-4 text-xs text-gray-500">
                          <span>
                            Current: {formatCurrency(rec.current_budget)}
                          </span>
                          <span>
                            Recommended: {formatCurrency(rec.recommended_budget)}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center justify-end gap-2">
                          <span className="text-xs text-gray-400">
                            Confidence: {(rec.confidence * 100).toFixed(0)}%
                          </span>
                          <span
                            className={`text-xs ${
                              rec.change_percent > 0
                                ? "text-green-500"
                                : "text-red-500"
                            }`}
                          >
                            {rec.change_percent > 0 ? "+" : ""}
                            {rec.change_percent.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    {/* Budget bar */}
                    <div className="mt-4">
                      <div className="flex h-2 overflow-hidden rounded-full bg-gray-100">
                        <div
                          className="bg-blue-500 transition-all"
                          style={{
                            width: `${(rec.current_budget / data.total_current_budget) * 100}%`,
                          }}
                        />
                      </div>
                      <div className="mt-1 flex justify-between text-[10px] text-gray-400">
                        <span>Current allocation</span>
                        <span>
                          {(rec.current_budget / data.total_current_budget * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
