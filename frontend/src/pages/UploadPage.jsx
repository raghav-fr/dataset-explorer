import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, FileSpreadsheet, Loader2, AlertCircle } from "lucide-react";
import { uploadDataset } from "../api/client.js";
import { useDataset } from "../context/DatasetContext.jsx";

export default function UploadPage() {
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { setDataset } = useDataset();
  const navigate = useNavigate();

  const handleFile = useCallback(
    async (file) => {
      if (!file) return;
      setLoading(true);
      setError(null);
      try {
        const data = await uploadDataset(file);
        setDataset(data);
        navigate("/dashboard");
      } catch (err) {
        setError(err?.response?.data?.detail || "Failed to upload dataset.");
      } finally {
        setLoading(false);
      }
    },
    [setDataset, navigate]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  };

  return (
    <div className="h-full flex flex-col items-center justify-center px-6">
      <div className="max-w-xl w-full">
        <p className="font-mono text-xs uppercase tracking-widest text-amber-400 mb-2">
          Step 1 of 3
        </p>
        <h1 className="text-2xl font-semibold mb-2">Upload a dataset</h1>
        <p className="text-ink-300 text-sm mb-8">
          CSV, Excel, JSON, or Parquet. We'll auto-detect encoding, delimiters,
          and column types, then clean it up before analysis.
        </p>

        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={onDrop}
          className={`flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-xl py-16 cursor-pointer transition-colors ${
            dragActive
              ? "border-amber-400 bg-panel2"
              : "border-line bg-panel hover:border-ink-500"
          }`}
        >
          <input
            type="file"
            className="hidden"
            accept=".csv,.xlsx,.xls,.json,.parquet"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
          {loading ? (
            <>
              <Loader2 className="animate-spin text-amber-400" size={28} />
              <p className="text-sm text-ink-300">
                Uploading and preprocessing&hellip;
              </p>
            </>
          ) : (
            <>
              <UploadCloud className="text-amber-400" size={28} />
              <p className="text-sm font-medium">
                Drop a file here, or click to browse
              </p>
              <p className="text-xs text-ink-500 font-mono">
                .csv &middot; .xlsx &middot; .json &middot; .parquet
              </p>
            </>
          )}
        </label>

        {error && (
          <div className="mt-4 flex items-start gap-2 text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-3 py-2">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="mt-8 flex items-center gap-2 text-xs text-ink-500">
          <FileSpreadsheet size={14} />
          Max file size is configured on the backend (default 200 MB).
        </div>
      </div>
    </div>
  );
}
