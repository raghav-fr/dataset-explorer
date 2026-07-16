import { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Loader2,
  Sparkles,
  RefreshCcw,
  CheckCircle2,
  CircleDot,
  AlertCircle,
  BarChart2,
  Brain,
  Zap,
  ScanLine,
} from "lucide-react";
import { useDataset } from "../context/DatasetContext.jsx";
import { getEDA, getExecutiveSummary } from "../api/client.js";
import LazyChartCard from "../components/LazyChartCard.jsx";
import StatTile from "../components/StatTile.jsx";
import { ErrorBoundary } from "../components/ErrorBoundary.jsx";
import { optimizeEdaPayload } from "../utils/blobUtils.js";

/* ── Phase classification ─────────────────────────────────── */
function classifyMsg(msg) {
  const m = msg.toLowerCase();
  if (m.includes("connect") || m.includes("dimension") || m.includes("summary stat"))
    return "init";
  if (m.includes("plan") || m.includes("optimal visual"))
    return "plan";
  if (m.includes("generating visual") || m.includes("generating chart"))
    return "chart";
  if (m.includes("completed visual") || m.includes("completed chart") || m.includes("✓"))
    return "done";
  if (m.includes("insight") || m.includes("crafting ai") || m.includes("analyzing chart"))
    return "ai";
  if (m.includes("correlation"))
    return "correlation";
  return "info";
}

const ICONS = {
  init:        <ScanLine  size={12} className="text-sky-400    shrink-0 mt-[3px]" />,
  plan:        <Zap       size={12} className="text-purple-400 shrink-0 mt-[3px]" />,
  chart:       <BarChart2 size={12} className="text-amber-400  shrink-0 mt-[3px]" />,
  done:        <CheckCircle2 size={12} className="text-emerald-400 shrink-0 mt-[3px]" />,
  ai:          <Brain     size={12} className="text-pink-400   shrink-0 mt-[3px]" />,
  correlation: <CircleDot size={12} className="text-cyan-400   shrink-0 mt-[3px]" />,
  info:        <CircleDot size={12} className="text-slate-400  shrink-0 mt-[3px]" />,
};

const COLORS = {
  init:        "text-sky-300",
  plan:        "text-purple-300",
  chart:       "text-amber-300",
  done:        "text-emerald-400 font-medium",
  ai:          "text-pink-300",
  correlation: "text-cyan-300",
  info:        "text-slate-400",
};

/* ── Progress extraction ──────────────────────────────────── */
function getProgress(logs) {
  for (let i = logs.length - 1; i >= 0; i--) {
    const m = logs[i].text.match(/(\d+)\s*\/\s*(\d+)/);
    if (m) return { current: +m[1], total: +m[2] };
  }
  return null;
}

/* ── Live terminal panel ──────────────────────────────────── */
function LiveTerminal({ logs }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const progress = getProgress(logs);
  const pct = progress
    ? Math.min(100, Math.round((progress.current / progress.total) * 100))
    : null;

  return (
    <div className="w-full max-w-xl mx-auto select-none">
      {/* header */}
      <div className="flex items-center gap-3 mb-4">
        <Loader2 className="animate-spin text-amber-400 shrink-0" size={22} />
        <div>
          <p className="text-sm font-semibold text-ink-100">Running AI-Powered EDA</p>
          <p className="text-xs text-ink-400">Generating charts &amp; crafting insights…</p>
        </div>
      </div>

      {/* progress bar */}
      {pct !== null && (
        <div className="mb-3">
          <div className="flex justify-between text-[11px] text-ink-500 mb-1">
            <span>Visualizations</span>
            <span>{progress.current} / {progress.total} &nbsp;({pct}%)</span>
          </div>
          <div className="h-1 w-full bg-panel2 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500 ease-out"
              style={{
                width: `${pct}%`,
                background: "linear-gradient(90deg, #f59e0b, #fbbf24)",
              }}
            />
          </div>
        </div>
      )}

      {/* terminal */}
      <div
        className="rounded-lg overflow-hidden border border-line shadow-xl"
        style={{ background: "#0c0e16" }}
      >
        {/* title bar */}
        <div
          className="flex items-center gap-1.5 px-3 py-2 border-b border-line"
          style={{ background: "#141620" }}
        >
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: "#ff5f57" }} />
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: "#ffbd2e" }} />
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: "#28c840" }} />
          <span className="ml-3 text-[11px] text-slate-500 font-mono">
            eda_engine &bull; live output
          </span>
        </div>

        {/* log body */}
        <div className="p-3 font-mono text-[11px] leading-5 overflow-y-auto space-y-1"
          style={{ maxHeight: "280px" }}>
          {logs.length === 0 && (
            <div className="text-slate-600 italic">Waiting for first event…</div>
          )}
          {logs.map((entry, i) => {
            const isActive = i === logs.length - 1;
            return (
              <div
                key={i}
                className="flex items-start gap-2"
                style={{ opacity: isActive ? 1 : 0.65 }}
              >
                {ICONS[entry.phase]}
                <span className="text-slate-600 shrink-0">{entry.time}</span>
                <span className={`flex-1 ${isActive ? COLORS[entry.phase] : "text-slate-400"}`}>
                  {entry.text}
                </span>
                {isActive && (
                  <span
                    className="text-amber-400 shrink-0 animate-pulse"
                    style={{ animationDuration: "0.8s" }}
                  >
                    ▋
                  </span>
                )}
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}

/* ── Main dashboard ───────────────────────────────────────── */
function Dashboard() {
  const { dataset, eda, setEda, summary, setSummary } = useDataset();
  const navigate = useNavigate();

  const [phase, setPhase] = useState("loading"); // "loading" | "done" | "error"
  const [errorMsg, setErrorMsg] = useState("");
  const [logs, setLogs] = useState([
    { text: "Connecting to AI EDA engine…", phase: "init", time: nowTime() },
  ]);

  // Use a ref to hold the addLog function so the callback in getEDA
  // always has a fresh reference without re-creating it on every render.
  const logsRef = useRef(logs);
  logsRef.current = logs;

  const pushLog = useCallback((text) => {
    const entry = { text, phase: classifyMsg(text), time: nowTime() };
    setLogs((prev) => [...prev, entry]);
  }, []);

  const runEda = useCallback(async () => {
    setPhase("loading");
    setErrorMsg("");
    setLogs([{ text: "Connecting to AI EDA engine…", phase: "init", time: nowTime() }]);

    // Parallel: kick off executive summary (cached, fast)
    if (!summary) {
      getExecutiveSummary(dataset.dataset_id)
        .then((r) => setSummary(r.executive_summary))
        .catch(console.error);
    }

    try {
      const result = await getEDA(dataset.dataset_id, true, pushLog);
      pushLog("✓ Analysis complete — rendering dashboard…");
      setEda(optimizeEdaPayload(result));
      setPhase("done");
    } catch (err) {
      console.error("EDA error:", err);
      setErrorMsg(err.message || "Failed to run EDA.");
      setPhase("error");
    }
  }, [dataset, summary, pushLog, setEda, setSummary]);

  // Run once when component mounts (or when eda is cleared for a re-run)
  const hasRun = useRef(false);
  useEffect(() => {
    if (!dataset) {
      navigate("/");
      return;
    }
    if (eda) {
      setPhase("done");
      return;
    }
    if (hasRun.current) return;
    hasRun.current = true;
    runEda();
  }, [dataset, eda, navigate, runEda]);

  if (!dataset) return null;

  /* ── split custom analyses by type ── */
  const custom = eda?.custom_analyses ?? [];
  const bivariate = custom.filter((a) => a?.type === "bivariate");
  const multivariate = custom.filter((a) => a?.type === "multivariate");
  const other = custom.filter((a) => a?.type !== "bivariate" && a?.type !== "multivariate");

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* header row */}
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
        {phase !== "loading" && (
          <button
            onClick={() => {
              hasRun.current = false;
              setEda(null);
              setSummary(null);
              runEda();
            }}
            className="flex items-center gap-2 text-xs text-ink-300 hover:text-ink-100 border border-line rounded-md px-3 py-1.5 transition-colors"
          >
            <RefreshCcw size={13} /> Re-run
          </button>
        )}
      </div>

      {/* ── loading state ── */}
      {phase === "loading" && (
        <div className="py-8">
          <LiveTerminal logs={logs} />
        </div>
      )}

      {/* ── error state ── */}
      {phase === "error" && (
        <div className="flex items-start gap-2 text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-4 py-3 mb-6">
          <AlertCircle size={15} className="shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* ── dashboard ── */}
      {phase === "done" && eda && (
        <div className="space-y-8">
          {summary && (
            <div className="bg-panel border border-amber-400/30 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={16} className="text-amber-400" />
                <p className="text-sm font-medium">Executive Summary</p>
              </div>
              <p className="text-sm text-ink-300 leading-relaxed">{summary}</p>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatTile label="Rows" value={(eda.summary?.rows ?? 0).toLocaleString()} />
            <StatTile label="Columns" value={eda.summary?.columns ?? 0} />
            <StatTile label="Memory" value={`${eda.summary?.memory_mb ?? 0} MB`} />
            <StatTile
              label="Missing values"
              value={(eda.summary?.missing_values_total ?? 0).toLocaleString()}
              accent={(eda.summary?.missing_values_total ?? 0) > 0}
            />
            <StatTile
              label="Duplicate rows"
              value={(eda.summary?.duplicate_rows ?? 0).toLocaleString()}
              accent={(eda.summary?.duplicate_rows ?? 0) > 0}
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

          {(eda.numerical_columns?.length ?? 0) > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Numerical Columns
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {eda.numerical_columns.map((col) => (
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

          {(eda.categorical_columns?.length ?? 0) > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Categorical Columns
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {eda.categorical_columns.map((col) => (
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

          {bivariate.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Bivariate Analysis
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {bivariate.map((a, i) => (
                  <LazyChartCard
                    key={i}
                    title={a.title}
                    subtitle={a.reasoning}
                    chart={a.chart}
                    aiInsight={a.ai_insight}
                  />
                ))}
              </div>
            </section>
          )}

          {multivariate.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Multivariate Analysis
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {multivariate.map((a, i) => (
                  <LazyChartCard
                    key={i}
                    title={a.title}
                    subtitle={a.reasoning}
                    chart={a.chart}
                    aiInsight={a.ai_insight}
                  />
                ))}
              </div>
            </section>
          )}

          {other.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-ink-100 mb-3 uppercase tracking-wide">
                Additional Analysis
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                {other.map((a, i) => (
                  <LazyChartCard
                    key={i}
                    title={a.title}
                    subtitle={a.reasoning}
                    chart={a.chart}
                    aiInsight={a.ai_insight}
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

function nowTime() {
  return new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export default function DashboardPage() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}
