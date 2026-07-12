import Plot from "react-plotly.js";

const darkLayoutOverrides = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: { color: "#b7bccb", family: "Inter, system-ui, sans-serif", size: 12 },
  margin: { t: 40, r: 20, b: 40, l: 50 },
  xaxis: { gridcolor: "#2b2f3c", zerolinecolor: "#2b2f3c" },
  yaxis: { gridcolor: "#2b2f3c", zerolinecolor: "#2b2f3c" },
};

export default function ChartCard({ title, subtitle, chart, aiInsight, height = 320 }) {
  if (!chart) return null;

  if (chart.type === "image") {
    return (
      <div className="bg-panel border border-line rounded-lg p-4 flex flex-col justify-between h-full">
        <div>
          {title && (
            <p className="text-sm font-medium text-ink-100 mb-0.5">{title}</p>
          )}
          {subtitle && (
            <p className="text-xs text-ink-500 mb-3 italic">{subtitle}</p>
          )}
          <div className="flex justify-center items-center overflow-hidden rounded bg-canvas/30" style={{ minHeight: height }}>
            <img 
              src={chart.src} 
              alt={title || "Chart"} 
              className="max-w-full max-h-full object-contain rounded" 
              style={{ maxHeight: height }} 
            />
          </div>
        </div>
        {aiInsight && (
          <div className="mt-3 pt-3 border-t border-line">
            <p className="text-xs font-mono text-amber-400 mb-1">AI INSIGHT</p>
            <p className="text-sm text-ink-300 leading-relaxed">{aiInsight}</p>
          </div>
        )}
      </div>
    );
  }

  const layout = { ...chart.layout, ...darkLayoutOverrides, title: undefined };

  return (
    <div className="bg-panel border border-line rounded-lg p-4 flex flex-col justify-between h-full">
      <div>
        {title && (
          <p className="text-sm font-medium text-ink-100 mb-0.5">{title}</p>
        )}
        {subtitle && (
          <p className="text-xs text-ink-500 mb-3 italic">{subtitle}</p>
        )}
        <Plot
          data={chart.data}
          layout={{ ...layout, autosize: true, height }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: "100%" }}
          useResizeHandler
        />
      </div>
      {aiInsight && (
        <div className="mt-3 pt-3 border-t border-line">
          <p className="text-xs font-mono text-amber-400 mb-1">AI INSIGHT</p>
          <p className="text-sm text-ink-300 leading-relaxed">{aiInsight}</p>
        </div>
      )}
    </div>
  );
}
