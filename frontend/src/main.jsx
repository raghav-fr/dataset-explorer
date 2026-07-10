import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App.jsx";
import { DatasetProvider } from "./context/DatasetContext.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <DatasetProvider>
        <App />
      </DatasetProvider>
    </BrowserRouter>
  </React.StrictMode>
);
