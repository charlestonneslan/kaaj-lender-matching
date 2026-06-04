import { NavLink, Route, Routes } from "react-router-dom";
import ApplicationsList from "./pages/ApplicationsList";
import NewApplication from "./pages/NewApplication";
import ApplicationDetail from "./pages/ApplicationDetail";
import LendersList from "./pages/LendersList";
import LenderDetail from "./pages/LenderDetail";

const navLink = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded text-sm ${
    isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-200"
  }`;

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <h1 className="text-lg font-semibold">Kaaj Lender Matching</h1>
            <nav className="flex gap-2">
              <NavLink to="/" end className={navLink}>
                Applications
              </NavLink>
              <NavLink to="/new" className={navLink}>
                New Application
              </NavLink>
              <NavLink to="/lenders" className={navLink}>
                Lenders
              </NavLink>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto w-full px-6 py-6 flex-1">
        <Routes>
          <Route path="/" element={<ApplicationsList />} />
          <Route path="/new" element={<NewApplication />} />
          <Route path="/applications/:id" element={<ApplicationDetail />} />
          <Route path="/lenders" element={<LendersList />} />
          <Route path="/lenders/:id" element={<LenderDetail />} />
        </Routes>
      </main>
    </div>
  );
}
