import { createContext, useContext, useState, useEffect } from "react";

const DatasetContext = createContext(null);

export function DatasetProvider({ children }) {
  const [dataset, setDataset] = useState(() => {
    const saved = sessionStorage.getItem("de_dataset");
    return saved ? JSON.parse(saved) : null;
  });

  const [eda, setEda] = useState(() => {
    const saved = sessionStorage.getItem("de_eda");
    return saved ? JSON.parse(saved) : null;
  });

  const [summary, setSummary] = useState(() => {
    const saved = sessionStorage.getItem("de_summary");
    return saved ? JSON.parse(saved) : null;
  });

  const [indexed, setIndexed] = useState(() => {
    const saved = sessionStorage.getItem("de_indexed");
    return saved ? JSON.parse(saved) === "true" : false;
  });

  const [messages, setMessages] = useState(() => {
    const saved = sessionStorage.getItem("de_messages");
    return saved ? JSON.parse(saved) : [];
  });

  // Sync states to sessionStorage on change
  useEffect(() => {
    if (dataset) {
      sessionStorage.setItem("de_dataset", JSON.stringify(dataset));
    } else {
      sessionStorage.removeItem("de_dataset");
    }
  }, [dataset]);

  useEffect(() => {
    if (eda) {
      sessionStorage.setItem("de_eda", JSON.stringify(eda));
    } else {
      sessionStorage.removeItem("de_eda");
    }
  }, [eda]);

  useEffect(() => {
    if (summary) {
      sessionStorage.setItem("de_summary", JSON.stringify(summary));
    } else {
      sessionStorage.removeItem("de_summary");
    }
  }, [summary]);

  useEffect(() => {
    sessionStorage.setItem("de_indexed", indexed ? "true" : "false");
  }, [indexed]);

  useEffect(() => {
    sessionStorage.setItem("de_messages", JSON.stringify(messages));
  }, [messages]);

  // Special setter to change/clear dataset and reset other states
  const changeDataset = (newDataset) => {
    setDataset(newDataset);
    setEda(null);
    setSummary(null);
    setIndexed(false);
    setMessages([]);
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
        indexed,
        setIndexed,
        messages,
        setMessages,
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
