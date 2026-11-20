import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

const PAGE_SIZE = 10;

export function RiskListPage() {
  const [window, setWindow] = useState("W8");
  const [flaggedOnly, setFlaggedOnly] = useState(true);
  const [offset, setOffset] = useState(0);
  const [searchInput, setSearchInput] = useState("");
  const [searchId, setSearchId] = useState<number | null>(null);

  const windowsQuery = useQuery({ queryKey: ["windows"], queryFn: api.windows });

  const studentsQuery = useQuery({
    queryKey: ["students", window, flaggedOnly, offset, searchId],
    queryFn: () => api.students(window, flaggedOnly, PAGE_SIZE, offset, searchId),
  });

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = searchInput.trim();
    if (trimmed === "") {
      setSearchId(null);
    } else {
      const parsed = Number(trimmed);
      setSearchId(Number.isFinite(parsed) ? parsed : null);
    }
    setOffset(0);
  }

  function handleWindowChange(w: string) {
    setWindow(w);
    setOffset(0);
  }

  const total = studentsQuery.data?.total ?? 0;
  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const hasPrev = offset > 0;
  const hasNext = offset + PAGE_SIZE < total;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Student Triage</h1>
        <p className="text-sm text-gray-500 mt-1">
          Review students flagged for intervention, ordered by highest risk.
        </p>
      </div>

      {/* FILTROS E PESQUISA */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">
            Observation Window:
            <select
              value={window}
              onChange={(e) => handleWindowChange(e.target.value)}
              className="ml-2 border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-gray-900 focus:border-gray-900 outline-none"
            >
              {(windowsQuery.data ?? []).map((w) => (
                <option key={w} value={w}>{w}</option>
              ))}
            </select>
          </label>

          <label className="text-sm font-medium text-gray-700 flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={flaggedOnly}
              onChange={(e) => { setFlaggedOnly(e.target.checked); setOffset(0); }}
              className="w-4 h-4 text-gray-900 rounded border-gray-300 focus:ring-gray-900"
            />
            Show flagged only
          </label>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              inputMode="numeric"
              placeholder="Search Student ID..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="border border-gray-300 rounded-lg pl-9 pr-3 py-1.5 text-sm w-56 focus:ring-2 focus:ring-gray-900 focus:border-gray-900 outline-none"
            />
          </div>
          <button
            type="submit"
            className="bg-gray-900 text-white text-sm rounded-lg px-4 py-1.5 font-medium hover:bg-gray-800 transition-colors"
          >
            Search
          </button>
          {searchId !== null && (
            <button
              type="button"
              onClick={() => { setSearchInput(""); setSearchId(null); setOffset(0); }}
              className="text-sm text-gray-500 hover:text-gray-900 underline px-2"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* TABELA */}
      {studentsQuery.isLoading && <p className="text-center py-10 text-gray-500">Loading data…</p>}
      {studentsQuery.isError && <p className="text-center py-10 text-red-600">Failed to load students.</p>}

      {studentsQuery.data && (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-600">
              <tr>
                <th className="px-6 py-4 font-medium">Student ID</th>
                <th className="px-6 py-4 font-medium">Presentation</th>
                <th className="px-6 py-4 font-medium">Risk Level</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {studentsQuery.data.items.map((s) => {
                const riskPct = Math.round(s.risk_score * 100);
                const isHigh = riskPct > 70;
                const isMed = riskPct > 40 && riskPct <= 70;

                return (
                  <tr key={`${s.student_id}-${s.presentation}`} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-gray-900">{s.student_id}</td>
                    <td className="px-6 py-4 text-gray-600">{s.presentation}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <span className="font-bold w-9 text-right">{riskPct}%</span>
                        <div className="w-24 bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-2 rounded-full ${isHigh ? 'bg-red-600' : isMed ? 'bg-yellow-500' : 'bg-green-500'}`}
                            style={{ width: `${riskPct}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {s.flagged ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          <AlertCircle className="w-3.5 h-3.5" /> Flagged
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Safe
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/students/${s.student_id}/${window}`}
                        className="inline-flex items-center justify-center bg-white border border-gray-300 text-gray-700 rounded-lg px-4 py-1.5 text-sm font-medium hover:bg-gray-50 hover:text-gray-900 transition-colors shadow-sm"
                      >
                        Review Profile
                      </Link>
                    </td>
                  </tr>
                );
              })}
              {studentsQuery.data.items.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                    No students match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* PAGINAÇÃO */}
      {studentsQuery.data && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-sm text-gray-500">
            Showing <span className="font-medium text-gray-900">{studentsQuery.data.items.length}</span> of{" "}
            <span className="font-medium text-gray-900">{total}</span> students
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              disabled={!hasPrev}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>
            <span className="text-sm text-gray-600 px-2">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setOffset(offset + PAGE_SIZE)}
              disabled={!hasNext}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50 transition-colors"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}