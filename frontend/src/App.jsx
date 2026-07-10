import { Routes, Route, NavLink } from "react-router-dom";
import { LayoutGrid, UploadCloud, MessagesSquare, ScanLine } from "lucide-react";
import UploadPage from "./pages/UploadPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";

const navItems = [
  { to: "/", label: "Upload", icon: UploadCloud, end: true },
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { to: "/chat", label: "Ask the data", icon: MessagesSquare },
];

function App() {
  return (
    <div className="min-h-screen bg-canvas text-ink-100 flex">
      <aside className="w-60 shrink-0 border-r border-line bg-panel flex flex-col">
        <div className="px-5 py-6 flex items-center gap-2 border-b border-line">
          <ScanLine className="text-amber-400" size={22} />
          <div>
            <p className="font-semibold tracking-tight leading-none">Dataset</p>
            <p className="font-semibold tracking-tight leading-none text-amber-400">
              Explorer
            </p>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-panel2 text-amber-400"
                    : "text-ink-300 hover:bg-panel2 hover:text-ink-100"
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-line text-xs text-ink-500 font-mono">
          Phase 1 build &middot; v0.1.0
        </div>
      </aside>

      <main className="flex-1 min-w-0 bg-dot-grid">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
