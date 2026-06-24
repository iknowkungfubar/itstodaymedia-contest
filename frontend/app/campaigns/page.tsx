"use client";

import { useEffect, useState } from "react";
import { Megaphone, RefreshCw } from "lucide-react";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { fetchCampaigns, triggerSync } from "@/lib/api";
import type { Campaign } from "@/lib/types";
import {
  formatCurrency,
  formatDate,
  formatNumber,
  formatPercent,
  formatRoas,
  getPlatformLabel,
} from "@/lib/utils";

const statusBadge = (status: string) => {
  const variants: Record<string, "success" | "warning" | "secondary" | "outline"> = {
    active: "success",
    paused: "warning",
    completed: "secondary",
    archived: "outline",
  };
  return variants[status] || "secondary";
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [platform, setPlatform] = useState("");
  const [status, setStatus] = useState("");
  const [syncing, setSyncing] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCampaigns({
        platform: platform || undefined,
        status: status || undefined,
        sort_by: "roas",
        sort_order: "desc",
      });
      setCampaigns(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load campaigns:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [platform, status]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSync() {
    setSyncing(true);
    try {
      await triggerSync();
      await load();
    } catch (err) {
      console.error("Sync failed:", err);
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Campaigns</h2>
          <p className="text-sm text-gray-500">{total} total campaigns</p>
        </div>
        <Button onClick={handleSync} disabled={syncing}>
          <RefreshCw
            className={`mr-2 h-4 w-4 ${syncing ? "animate-spin" : ""}`}
          />
          {syncing ? "Syncing..." : "Sync Platforms"}
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select
          options={[
            { value: "", label: "All Platforms" },
            { value: "meta", label: "Meta Ads" },
            { value: "google", label: "Google Ads" },
            { value: "taboola", label: "Taboola" },
            { value: "tiktok", label: "TikTok Ads" },
          ]}
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
        />
        <Select
          options={[
            { value: "", label: "All Status" },
            { value: "active", label: "Active" },
            { value: "paused", label: "Paused" },
            { value: "completed", label: "Completed" },
          ]}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        />
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
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
                  onClick={() => load()}
                >
                  Retry
                </Button>
              </div>
            </div>
          ) : campaigns.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-sm text-gray-500">
              No campaigns found. Sync your platforms to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Name</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Platform</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Spent</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Revenue</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">ROAS</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">CPA</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">CTR</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Conversions</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((c) => (
                    <tr
                      key={c.id}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">
                        <div className="flex items-center gap-2">
                          <Megaphone className="h-4 w-4 text-gray-400" />
                          {c.name}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{getPlatformLabel(c.platform)}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={statusBadge(c.status)}>
                          {c.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {formatCurrency(c.spent)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {formatCurrency(c.revenue)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm font-medium">
                        {formatRoas(c.roas)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {c.cpa ? formatCurrency(c.cpa) : "-"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {c.ctr ? formatPercent(c.ctr) : "-"}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">
                        {formatNumber(c.conversions)}
                      </td>
                      <td className="px-4 py-3 text-right text-xs text-gray-500">
                        {formatDate(c.created_at)}
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
