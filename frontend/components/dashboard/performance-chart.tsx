"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CampaignSummary } from "@/lib/types";
import { formatCurrency, getPlatformLabel } from "@/lib/utils";

export function PerformanceChart({
  summary,
}: {
  summary: CampaignSummary;
}) {
  const data = Object.entries(summary.by_platform).map(
    ([platform, values]) => ({
      name: getPlatformLabel(platform),
      Spend: values.spent,
      Revenue: values.revenue,
    })
  );

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-sm text-gray-500">No platform data available</p>
      </div>
    );
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12, fill: "#6b7280" }}
            axisLine={{ stroke: "#e5e7eb" }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "#6b7280" }}
            axisLine={{ stroke: "#e5e7eb" }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip
            formatter={(value) => [
              typeof value === "number" ? formatCurrency(value) : String(value),
              undefined,
            ]}
            contentStyle={{
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
              boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
            }}
          />
          <Bar
            dataKey="Spend"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
            maxBarSize={40}
          />
          <Bar
            dataKey="Revenue"
            fill="#10b981"
            radius={[4, 4, 0, 0]}
            maxBarSize={40}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
