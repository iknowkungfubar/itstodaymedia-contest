"use client";

import { useCallback, useEffect, useState } from "react";
import { Sparkles, FileText } from "lucide-react";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchCreatives, analyzeCreatives } from "@/lib/api";
import type { Creative, CreativeAnalysisResult } from "@/lib/types";
import { formatCurrency, formatPercent, formatRoas } from "@/lib/utils";

export default function CreativesPage() {
  const [creatives, setCreatives] = useState<Creative[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<Map<number, CreativeAnalysisResult>>(
    new Map()
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCreatives();
      setCreatives(data);
    } catch (err) {
      console.error("Failed to load creatives:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function handleAnalyze() {
    const ids = creatives.map((c) => c.id);
    if (ids.length === 0) return;

    setAnalyzing(true);
    try {
      const analysisResults = await analyzeCreatives(ids);
      const map = new Map<number, CreativeAnalysisResult>();
      for (const r of analysisResults) {
        map.set(r.creative_id, r);
      }
      setResults(map);
    } catch (err) {
      console.error("Analysis failed:", err);
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Creative Analyzer
          </h2>
          <p className="text-sm text-gray-500">
            AI-powered performance analysis of your ad creatives
          </p>
        </div>
        <Button onClick={handleAnalyze} disabled={analyzing || creatives.length === 0}>
          <Sparkles className={`mr-2 h-4 w-4 ${analyzing ? "animate-pulse" : ""}`} />
          {analyzing ? "Analyzing..." : "Analyze All Creatives"}
        </Button>
      </div>

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
          ) : creatives.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-sm text-gray-500">
              No creatives found. Add creatives to campaigns first.
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {creatives.map((c) => {
                const analysis = results.get(c.id);
                return (
                  <div key={c.id} className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <FileText className="mt-1 h-5 w-5 text-gray-400" />
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {c.headline}
                          </h3>
                          {c.body && (
                            <p className="mt-1 text-sm text-gray-500">
                              {c.body}
                            </p>
                          )}
                          <div className="mt-2 flex flex-wrap gap-2">
                            <Badge variant="outline">{c.platform}</Badge>
                            {c.cta && (
                              <Badge variant="secondary">{c.cta}</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      {analysis && (
                        <div className="shrink-0 text-right">
                          <div className="text-2xl font-bold text-blue-600">
                            {(analysis.ai_score * 100).toFixed(0)}
                          </div>
                          <div className="text-xs text-gray-500">AI Score</div>
                        </div>
                      )}
                    </div>

                    {/* Performance metrics */}
                    <div className="mt-4 grid grid-cols-3 gap-4 sm:grid-cols-5">
                      <div>
                        <p className="text-xs text-gray-500">Impressions</p>
                        <p className="font-medium text-gray-900">
                          {c.impressions.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">CTR</p>
                        <p className="font-medium text-gray-900">
                          {c.ctr ? formatPercent(c.ctr) : "-"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">CPA</p>
                        <p className="font-medium text-gray-900">
                          {c.cpa ? formatCurrency(c.cpa) : "-"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">ROAS</p>
                        <p className="font-medium text-gray-900">
                          {formatRoas(c.roas)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Spend</p>
                        <p className="font-medium text-gray-900">
                          {formatCurrency(c.spend)}
                        </p>
                      </div>
                    </div>

                    {/* AI Analysis results */}
                    {analysis && (
                      <div className="mt-4 rounded-lg bg-gray-50 p-4">
                        <div className="grid gap-4 md:grid-cols-3">
                          <div>
                            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-green-600">
                              Strengths
                            </h4>
                            <ul className="space-y-1">
                              {analysis.strengths.map((s, i) => (
                                <li
                                  key={i}
                                  className="text-sm text-gray-700"
                                >
                                  ✓ {s}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-red-600">
                              Weaknesses
                            </h4>
                            <ul className="space-y-1">
                              {analysis.weaknesses.map((w, i) => (
                                <li
                                  key={i}
                                  className="text-sm text-gray-700"
                                >
                                  ✗ {w}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-blue-600">
                              Recommendations
                            </h4>
                            <ul className="space-y-1">
                              {analysis.recommendations.map((r, i) => (
                                <li
                                  key={i}
                                  className="text-sm text-gray-700"
                                >
                                  → {r}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                        {(analysis.predicted_ctr !== null ||
                          analysis.predicted_conversion_rate !== null) && (
                          <div className="mt-3 flex gap-6 border-t border-gray-200 pt-3">
                            {analysis.predicted_ctr !== null && (
                              <div>
                                <span className="text-xs text-gray-500">
                                  Predicted CTR:{" "}
                                </span>
                                <span className="font-medium text-gray-900">
                                  {(analysis.predicted_ctr * 100).toFixed(2)}%
                                </span>
                              </div>
                            )}
                            {analysis.predicted_conversion_rate !== null && (
                              <div>
                                <span className="text-xs text-gray-500">
                                  Predicted Conv Rate:{" "}
                                </span>
                                <span className="font-medium text-gray-900">
                                  {(
                                    analysis.predicted_conversion_rate * 100
                                  ).toFixed(2)}
                                  %
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
