import { createContext, useContext, useState, useEffect } from "react";

const DatasetContext = createContext(null);

export function DatasetProvider({ children }) {
  const [dataset, setDataset] = useState(() => {
    const saved = sessionStorage.getItem("de_dataset");
    return saved ? JSON.parse(saved) : null;
  });

  // EDA is never persisted — base64 charts make it 10-50 MB, busting sessionStorage quota.
  const [eda, setEda] = useState(null);

  const [summary, setSummary] = useState(() => {
    const saved = sessionStorage.getItem("de_summary");
    return saved ? JSON.parse(saved) : null;
  });

  // Sync lightweight states to sessionStorage
  useEffect(() => {
    if (dataset) {
      sessionStorage.setItem("de_dataset", JSON.stringify(dataset));
    } else {
      sessionStorage.removeItem("de_dataset");
    }
  }, [dataset]);

  useEffect(() => {
    if (summary) {
      sessionStorage.setItem("de_summary", JSON.stringify(summary));
    } else {
      sessionStorage.removeItem("de_summary");
    }
  }, [summary]);

  // Special setter: changing the dataset resets all derived state
  const changeDataset = (newDataset) => {
    setDataset(newDataset);
    setEda(null);
    setSummary(null);
  };

  return (
    <DatasetContext.Provider
      value={{
        dataset,
        setDataset: changeDataset,
        eda,
        setEda,
        summary,
        setSummary,
      }}
    >
      {children}
    </DatasetContext.Provider>
  );
}

export function useDataset() {
  const ctx = useContext(DatasetContext);
  if (!ctx) throw new Error("useDataset must be used within DatasetProvider");
  return ctx;
}
