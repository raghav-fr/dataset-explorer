import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Send, Loader2, DatabaseZap, ChevronDown, ChevronUp } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useDataset } from "../context/DatasetContext.jsx";
import { indexDatasetForChat, askQuestion, getIndexStatus } from "../api/client.js";

export default function ChatPage() {
  const { dataset, indexed, setIndexed, messages, setMessages } = useDataset();
  const navigate = useNavigate();
  const [indexing, setIndexing] = useState(false);
  const [input, setInput] = useState("");
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState(null);
  const [openSources, setOpenSources] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!dataset) {
      navigate("/");
      return;
    }

    async function checkIndex() {
      try {
        const status = await getIndexStatus(dataset.dataset_id);
        if (status.indexed) {
          setIndexed(true);
        }
      } catch (err) {
        console.error("Failed to check index status", err);
      }
    }

    if (!indexed) {
      checkIndex();
    }
  }, [dataset, indexed, navigate, setIndexed]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleIndex = async () => {
    setIndexing(true);
    setError(null);
    try {
      await indexDatasetForChat(dataset.dataset_id);
      setIndexed(true);
      setMessages([
        {
          role: "assistant",
          content:
            "Your dataset is indexed. Ask me anything — e.g. \"Which category has the highest average value?\" or \"Summarize the key trends.\"",
        },
      ]);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to index dataset.");
    } finally {
      setIndexing(false);
    }
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!input.trim() || asking) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setAsking(true);
    setError(null);
    try {
      const result = await askQuestion(dataset.dataset_id, question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, sources: result.used_chunks },
      ]);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to get an answer.");
    } finally {
      setAsking(false);
    }
  };

  if (!dataset) return null;

  return (
    <div className="h-screen flex flex-col max-w-3xl mx-auto">
      <div className="px-8 pt-8 pb-4">
        <p className="font-mono text-xs uppercase tracking-widest text-amber-400 mb-1">
          Step 3 of 3
        </p>
        <h1 className="text-2xl font-semibold">Ask the data</h1>
        <p className="text-ink-300 text-sm mt-1">{dataset.filename}</p>
      </div>

      {!indexed ? (
        <div className="flex-1 flex items-center justify-center px-8">
          <div className="text-center max-w-sm">
            <DatabaseZap className="mx-auto text-amber-400 mb-3" size={28} />
            <p className="text-sm text-ink-300 mb-4">
              Index this dataset into the vector store before chatting.
              We'll chunk column summaries and a representative row sample,
              embed them, and store them in Qdrant.
            </p>
            <button
              onClick={handleIndex}
              disabled={indexing}
              className="inline-flex items-center gap-2 bg-amber-400 text-canvas font-medium text-sm px-4 py-2 rounded-md hover:bg-amber-500 disabled:opacity-60"
            >
              {indexing && <Loader2 className="animate-spin" size={15} />}
              {indexing ? "Indexing…" : "Index dataset"}
            </button>
            {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
          </div>
        </div>
      ) : (
        <>
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-8 space-y-4">
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
                <div
                  className={`max-w-[85%] rounded-lg px-4 py-3 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-amber-400 text-canvas"
                      : "bg-panel border border-line text-ink-100"
                  }`}
                >
                  <ReactMarkdown>{m.content}</ReactMarkdown>
                  {m.sources && m.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-line/50">
                      <button
                        onClick={() => setOpenSources(openSources === i ? null : i)}
                        className="flex items-center gap-1 text-xs text-ink-500 hover:text-ink-300"
                      >
                        {openSources === i ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        {m.sources.length} source chunk(s)
                      </button>
                      {openSources === i && (
                        <div className="mt-2 space-y-1 font-mono text-xs text-ink-500 max-h-40 overflow-y-auto">
                          {m.sources.map((s, si) => (
                            <p key={si} className="whitespace-pre-wrap border-l-2 border-line pl-2">
                              {s}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {asking && (
              <div className="flex items-center gap-2 text-ink-500 text-sm">
                <Loader2 className="animate-spin" size={14} /> Thinking…
              </div>
            )}
          </div>

          <form onSubmit={handleAsk} className="px-8 py-4 border-t border-line flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your dataset…"
              className="flex-1 bg-panel border border-line rounded-md px-3 py-2 text-sm focus:outline-none focus:border-amber-400"
            />
            <button
              type="submit"
              disabled={asking || !input.trim()}
              className="bg-amber-400 text-canvas rounded-md px-3 py-2 disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </form>
        </>
      )}
    </div>
  );
}
