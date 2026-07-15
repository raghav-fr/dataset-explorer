import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Sparkles, RefreshCcw } from "lucide-react";
import { useDataset } from "../context/DatasetContext.jsx";
import { getEDA, getExecutiveSummary } from "../api/client.js";
import LazyChartCard from "../components/LazyChartCard.jsx";
import StatTile from "../components/StatTile.jsx";
import { ErrorBoundary } from "../components/ErrorBoundary.jsx";
import { optimizeEdaPayload } from "../utils/blobUtils.js";

function Dashboard() {
  const { dataset, eda, setEda, summary, setSummary } = useDataset();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(!eda || !summary);
  const [error, setError] = useState(null);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (!dataset) {
      navigate("/");
      return;
    }

    if (eda && summary) {
      setLoading(false);
      return;
    }

    if (fetchedRef.current) return;
    fetchedRef.current = true;

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [edaResult, summaryResult] = await Promise.all([
          getEDA(dataset.dataset_id, true),
          getExecutiveSummary(dataset.dataset_id),
        ]);
        if (!cancelled) {
          setEda(optimizeEdaPayload(edaResult));
          setSummary(summaryResult.executive_summary);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err?.response?.data?.detail || "Failed to run EDA.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [dataset, eda, summary, navigate, setEda, setSummary]);

  if (!dataset) return null;

  const customAnalyses = eda?.custom_analyses || [];
  const bivariateAnalyses = customAnalyses.filter((a) => a?.type === "bivariate");
  const multivariateAnalyses = customAnalyses.filter((a) => a?.type === "multivariate");
  const otherCustomAnalyses = customAnalyses.filter(
    (a) => a?.type !== "bivariate" && a?.type !== "multivariate"
  );

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-amber-400 mb-1">
            Step 2 of 3
          </p>
          <h1 className="text-2xl font-semibold">{dataset.filename}</h1>
          <p className="text-ink-300 text-sm mt-1">
            {dataset.rows.toLocaleString()} rows &middot; {dataset.columns} columns
          </p>
        </div>
        <button
          onClick={() => {
            setEda(null);
            setSummary(null);
          }}
          className="flex items-center gap-2 text-xs text-ink-300 hover:text-ink-100 border border-line rounded-md px-3 py-1.5"
        >
          <RefreshCcw size={13} /> Re-run
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-ink-300 text-sm py-12 justify-center">
          <Loader2 className="animate-spin" size={18} />
          Running EDA and generating AI insights&hellip; this can take a
          minute for large datasets.
        </div>
      )}

      {error && (
        <div className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-3 py-2 mb-6">
          {error}
        </div>
      )}

      {!loading && eda && (
        <div className="space-y-8">
          {summary && (
            <div className="bg-panel border border-amber-400/30 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={16} className="text-amber-400" />
                <p className="text-sm font-medium">Executive summary</p>
              </div>
              <p className="text-sm text-ink-300 leading-relaxed">{summary}</p>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatTile label="Rows" value={(eda.summary?.rows || 0).toLocaleString()} />
            <StatTile label="Columns" value={eda.summary?.columns || 0} />
            <StatTile
              label="Memory"
              value={`${eda.summary?.memory_mb || 0} MB`}
            />
            <StatTile
              label="Missing values"
              value={(eda.summary?.missing_values_total || 0).toLocaleString()}
              accent={eda.summary?.missing_values_total > 0}
            />
            <StatTile
              label="Duplicate rows"
              value={(eda.summary?.duplicate_rows || 0).toLocaleString()}
              accent={eda.summary?.duplicate_rows > 0}
            />
          </div>

          {eda.correlation && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Correlation
              </h2>
              <LazyChartCard
                chart={eda.correlation}
                aiInsight={eda.correlation_insight}
                height={420}
              />
            </section>
          )}

          {eda.numerical_columns?.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Numerical columns
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {eda.numerical_columns?.map((col) => (
                  <LazyChartCard
                    key={col.name}
                    title={col.name}
                    chart={col.chart}
                    aiInsight={col.ai_insight}
                  />
                ))}
              </div>
            </section>
          )}

          {eda.categorical_columns?.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Categorical columns
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {eda.categorical_columns?.map((col) => (
                  <LazyChartCard
                    key={col.name}
                    title={col.name}
                    chart={col.chart}
                    aiInsight={col.ai_insight}
                  />
                ))}
              </div>
            </section>
          )}

          {bivariateAnalyses.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Bivariate Analysis
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {bivariateAnalyses.map((analysis, idx) => (
                  <LazyChartCard
                    key={idx}
                    title={analysis.title}
                    subtitle={analysis.reasoning}
                    chart={analysis.chart}
                    aiInsight={analysis.ai_insight}
                  />
                ))}
              </div>
            </section>
          )}

          {multivariateAnalyses.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Multivariate Analysis
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {multivariateAnalyses.map((analysis, idx) => (
                  <LazyChartCard
                    key={idx}
                    title={analysis.title}
                    subtitle={analysis.reasoning}
                    chart={analysis.chart}
                    aiInsight={analysis.ai_insight}
                  />
                ))}
              </div>
            </section>
          )}

          {otherCustomAnalyses.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Additional Analysis
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {otherCustomAnalyses.map((analysis, idx) => (
                  <LazyChartCard
                    key={idx}
                    title={analysis.title}
                    subtitle={analysis.reasoning}
                    chart={analysis.chart}
                    aiInsight={analysis.ai_insight}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}
