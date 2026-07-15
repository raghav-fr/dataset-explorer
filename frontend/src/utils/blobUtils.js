/**
 * Converts a base64 data URI (e.g. data:image/png;base64,...) to a Blob URL.
 * This removes the massive string from the JS heap and offloads it to the browser's Blob storage.
 */
export function base64ToBlobUrl(base64Str) {
  try {
    const match = base64Str.match(/^data:([^;]+);base64,(.+)$/);
    if (!match) return base64Str;
    const contentType = match[1];
    const b64Data = match[2];
    
    // Decode base64 (using atob is fast enough for ~500kb strings)
    const byteCharacters = atob(b64Data);
    const byteArrays = [];
    
    // Process in chunks to prevent max call stack errors
    for (let offset = 0; offset < byteCharacters.length; offset += 1024) {
      const slice = byteCharacters.slice(offset, offset + 1024);
      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }
    
    const blob = new Blob(byteArrays, { type: contentType });
    return URL.createObjectURL(blob);
  } catch (e) {
    console.error("Failed to convert base64 to blob", e);
    return base64Str;
  }
}

/**
 * Recursively scans the eda payload and converts any huge Base64 charts to lightweight Blob URLs.
 * This prevents the React Context and Virtual DOM from blowing up browser memory limits (OOM crashes).
 */
export function optimizeEdaPayload(eda) {
  if (!eda) return eda;
  
  const processChart = (chart) => {
    if (chart && chart.type === "image" && chart.src && chart.src.startsWith("data:")) {
      chart.src = base64ToBlobUrl(chart.src);
    }
  };

  eda.numerical_columns?.forEach(c => processChart(c.chart));
  eda.categorical_columns?.forEach(c => processChart(c.chart));
  
  if (eda.correlation) {
    processChart(eda.correlation);
  }
  
  eda.custom_analyses?.forEach(a => processChart(a.chart));

  return eda;
}
