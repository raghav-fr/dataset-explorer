import { useState, useEffect, useRef } from "react";
import ChartCard from "./ChartCard.jsx";

export default function LazyChartCard(props) {
  const [isVisible, setIsVisible] = useState(false);
  const [renderedHeight, setRenderedHeight] = useState(400); // Reasonable default
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { rootMargin: "1200px" } // Load generously ahead of scroll
    );
    
    if (ref.current) {
      observer.observe(ref.current);
    }
    
    return () => {
      observer.disconnect();
    };
  }, []);

  // Track the actual rendered height to prevent layout thrashing and infinite loops
  useEffect(() => {
    if (isVisible && ref.current) {
      const ro = new ResizeObserver((entries) => {
        for (let e of entries) {
          if (e.target.offsetHeight > 50) {
            setRenderedHeight(e.target.offsetHeight);
          }
        }
      });
      ro.observe(ref.current);
      return () => ro.disconnect();
    }
  }, [isVisible]);

  return (
    <div ref={ref} style={{ minHeight: isVisible ? "auto" : renderedHeight, height: isVisible ? "100%" : renderedHeight }}>
      {isVisible ? (
        <ChartCard {...props} />
      ) : (
        <div 
          className="bg-panel border border-line rounded-lg flex items-center justify-center text-ink-500 animate-pulse w-full"
          style={{ height: "100%", minHeight: renderedHeight }}
        >
          Loading...
        </div>
      )}
    </div>
  );
}
