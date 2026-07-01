"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Bell, Info, Lightbulb, TrendingUp } from "lucide-react";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { fetchInsights, markInsightRead, scanForAnomalies } from "@/lib/api";
import type { Insight } from "@/lib/types";
import {
  formatDate,
  formatCurrency,
  formatNumber,
  formatPercent,
  getPlatformLabel,
  getSeverityColor,
} from "@/lib/utils";

const typeIcons: Record<string, React.ReactNode> = {
  anomaly: <AlertTriangle className="h-4 w-4" />,
  recommendation: <TrendingUp className="h-4 w-4" />,
  insight: <Lightbulb className="h-4 w-4" />,
  alert: <Bell className="h-4 w-4" />,
};

const severityBadge: Record<string, "destructive" | "warning" | "default" | "secondary"> = {
  critical: "destructive",
  high: "warning",
  medium: "default",
  low: "secondary",
  info: "secondary",
};

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchInsights({
        type: typeFilter || undefined,
        severity: severityFilter || undefined,
      });
      setInsights(data.items);
      setUnreadCount(data.unread_count);
    } catch (err) {
      console.error("Failed to load insights:", err);
    } finally {
      setLoading(false);
    }
  }, [typeFilter, severityFilter]);

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect */
    load();
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [load]);

  async function handleScan() {
    setScanning(true);
    try {
      await scanForAnomalies();
      await load();
    } catch (err) {
      console.error("Scan failed:", err);
    } finally {
      setScanning(false);
    }
  }

  async function handleMarkRead(id: number) {
    try {
      await markInsightRead(id);
      await load();
    } catch (err) {
      console.error("Failed to mark insight as read:", err);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Insights & Alerts</h2>
          <p className="text-sm text-gray-500">
            {insights.length} insights · {unreadCount} unread
          </p>
        </div>
        <Button onClick={handleScan} disabled={scanning}>
          <Bell className={`mr-2 h-4 w-4 ${scanning ? "animate-pulse" : ""}`} />
          {scanning ? "Scanning..." : "Scan for Anomalies"}
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select
          options={[
            { value: "", label: "All Types" },
            { value: "anomaly", label: "Anomalies" },
            { value: "recommendation", label: "Recommendations" },
            { value: "insight", label: "Insights" },
            { value: "alert", label: "Alerts" },
          ]}
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        />
        <Select
          options={[
            { value: "", label: "All Severities" },
            { value: "critical", label: "Critical" },
            { value: "high", label: "High" },
            { value: "medium", label: "Medium" },
            { value: "low", label: "Low" },
            { value: "info", label: "Info" },
          ]}
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
        />
      </div>

      {/* Insights list */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
            </div>
          ) : insights.length === 0 ? (
            <div className="flex h-64 items-center justify-center">
              <div className="text-center">
                <Info className="mx-auto h-8 w-8 text-gray-400" />
                <p className="mt-2 text-sm text-gray-500">
                  No insights yet. Run a scan to detect anomalies.
                </p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {insights.map((insight) => (
                <div
                  key={insight.id}
                  className={`p-5 ${!insight.is_read ? "bg-blue-50/50" : ""}`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`mt-0.5 shrink-0 rounded-lg p-2 ${getSeverityColor(insight.severity)}`}
                    >
                      {typeIcons[insight.type] || (
                        <Info className="h-4 w-4" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-gray-900">
                              {insight.title}
                            </h3>
                            {!insight.is_read && (
                              <span className="h-2 w-2 rounded-full bg-blue-500" />
                            )}
                          </div>
                          <p className="mt-1 text-sm text-gray-600">
                            {insight.description}
                          </p>
                        </div>
                      </div>
                      <div className="mt-3 flex flex-wrap items-center gap-3">
                        <Badge
                          variant={severityBadge[insight.severity] || "secondary"}
                        >
                          {insight.severity}
                        </Badge>
                        <Badge variant="outline">{insight.type}</Badge>
                        {!insight.is_read && (
                          <button
                            onClick={() => handleMarkRead(insight.id)}
                            className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
                          >
                            Mark as read
                          </button>
                        )}
                        {insight.platform && (
                          <span className="text-xs text-gray-400">
                            {getPlatformLabel(insight.platform)}
                          </span>
                        )}
                        {insight.campaign_name && (
                          <span className="text-xs text-gray-400">
                            {insight.campaign_name}
                          </span>
                        )}
                        {insight.metric_name && (
                          <span className="text-xs text-gray-400">
                            Metric: {insight.metric_name}
                          </span>
                        )}
                      </div>
                      {/* Metric values */}
                      {(() => {
                        const metricName = insight.metric_name;
                        const label =
                          metricName
                            ? metricName.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
                            : "Value";

                        function formatMetricValue(value: number): string {
                          const pctMetrics = ["ctr", "conversion_rate", "bounce_rate", "engagement_rate"];
                          const countMetrics = ["impressions", "clicks", "conversions", "reach", "frequency"];
                          if (pctMetrics.includes(metricName ?? "")) return formatPercent(value);
                          if (countMetrics.includes(metricName ?? "")) return formatNumber(value);
                          return formatCurrency(value);
                        }

                        return (insight.current_value !== null ||
                          insight.previous_value !== null ||
                          insight.threshold !== null) ? (
                          <div className="mt-3 flex gap-4 text-sm">
                            {insight.current_value !== null && (
                              <div>
                                <span className="text-xs text-gray-400">
                                  Current {label}:{" "}
                                </span>
                                <span className="font-mono font-medium text-gray-900">
                                  {formatMetricValue(insight.current_value)}
                                </span>
                              </div>
                            )}
                            {insight.previous_value !== null && (
                              <div>
                                <span className="text-xs text-gray-400">
                                  Previous {label}:{" "}
                                </span>
                                <span className="font-mono font-medium text-gray-900">
                                  {formatMetricValue(insight.previous_value)}
                                </span>
                              </div>
                            )}
                            {insight.threshold !== null && (
                              <div>
                                <span className="text-xs text-gray-400">
                                  Threshold {label}:{" "}
                                </span>
                                <span className="font-mono font-medium text-gray-900">
                                  {formatMetricValue(insight.threshold)}
                                </span>
                              </div>
                            )}
                          </div>
                        ) : null;
                      })()}
                      <p className="mt-2 text-xs text-gray-400">
                        {formatDate(insight.created_at)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
