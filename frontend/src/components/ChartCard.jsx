import Plot from "react-plotly.js";

const darkLayoutOverrides = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: { color: "#b7bccb", family: "Inter, system-ui, sans-serif", size: 12 },
  margin: { t: 40, r: 20, b: 40, l: 50 },
  xaxis: { gridcolor: "#2b2f3c", zerolinecolor: "#2b2f3c" },
  yaxis: { gridcolor: "#2b2f3c", zerolinecolor: "#2b2f3c" },
};

export default function ChartCard({ title, chart, aiInsight, height = 320 }) {
  if (!chart) return null;
  const layout = { ...chart.layout, ...darkLayoutOverrides, title: undefined };

  return (
    <div className="bg-panel border border-line rounded-lg p-4">
      {title && (
        <p className="text-sm font-medium text-ink-100 mb-1">{title}</p>
      )}
      <Plot
        data={chart.data}
        layout={{ ...layout, autosize: true, height }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
        useResizeHandler
      />
      {aiInsight && (
        <div className="mt-3 pt-3 border-t border-line">
          <p className="text-xs font-mono text-amber-400 mb-1">AI INSIGHT</p>
          <p className="text-sm text-ink-300 leading-relaxed">{aiInsight}</p>
        </div>
      )}
    </div>
  );
}
