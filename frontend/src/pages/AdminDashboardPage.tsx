import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis, YAxis,
} from "recharts";
import { api } from "../api/client";

export function AdminDashboardPage() {
  const [window, setWindow] = useState("W8");
  const windowsQuery = useQuery({ queryKey: ["windows"], queryFn: api.windows });
  
  // Pega as estatísticas da janela atual
  const statsQuery = useQuery({
    queryKey: ["stats", window],
    queryFn: () => api.admin.stats(window),
  });

  // NOVO: Pega as estatísticas de TODAS as janelas para o gráfico de evolução
  const allWindowsQuery = useQuery({
    queryKey: ["stats-all"],
    queryFn: async () => {
      const windows = await api.windows();
      return Promise.all(windows.map((w) => api.admin.stats(w)));
    },
  });

  // NOVO: Pega os top 5 alunos flagged para a tabela de prioridade
  const topStudentsQuery = useQuery({
    queryKey: ["students-top", window],
    queryFn: () => api.students(window, true, 5, 0), // 5 alunos, offset 0
  });

  if (statsQuery.isLoading || !statsQuery.data) return <p>Loading…</p>;
  
  const stats = statsQuery.data;

  // Dados para o gráfico de evolução
  const evolutionData = allWindowsQuery.data?.map((s) => ({
    window: s.window,
    flaggedPct: s.flagged_pct * 100,
  })) || [];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Admin Dashboard</h1>
        <label className="text-sm">
          Window:{" "}
          <select
            value={window}
            onChange={(e) => setWindow(e.target.value)}
            className="border border-gray-300 rounded px-2 py-1 ml-2"
          >
            {(windowsQuery.data ?? []).map((w) => (
              <option key={w} value={w}>{w}</option>
            ))}
          </select>
        </label>
      </div>

      {/* 1. KPIs CONTEXTUALIZADOS */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500">Total de Alunos</p>
          <p className="text-3xl font-bold">{stats.n_students}</p>
          <p className="text-xs text-gray-400 mt-1">Nesta janela</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 border-l-4 border-l-red-500">
          <p className="text-sm text-red-600 font-medium">Alunos em Risco</p>
          <p className="text-3xl font-bold">{stats.n_flagged}</p>
          <p className="text-xs text-red-500 mt-1">A necessitar de intervenção</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500">Taxa de Risco</p>
          <p className="text-3xl font-bold">{(stats.flagged_pct * 100).toFixed(1)}%</p>
          <p className="text-xs text-gray-400 mt-1">Da população nesta janela</p>
        </div>
      </div>

      {/* 2. TABELA DE AÇÃO PRIORITÁRIA E EVOLUÇÃO (lado a lado) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Ação Prioritária */}
        <section className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Prioridade de Intervenção</h2>
            <Link to="/" className="text-sm text-blue-600 hover:underline">Ver todos →</Link>
          </div>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-gray-500 border-b">
                <th className="pb-2">Aluno ID</th>
                <th className="pb-2">Risco</th>
                <th className="pb-2">Ação</th>
              </tr>
            </thead>
            <tbody>
              {topStudentsQuery.data?.items.map((s) => (
                <tr key={s.student_id} className="border-b last:border-0">
                  <td className="py-2 font-mono">{s.student_id}</td>
                  <td className="py-2 font-bold text-red-600">{(s.risk_score * 100).toFixed(0)}%</td>
                  <td className="py-2">
                    <Link to={`/students/${s.student_id}/${window}`} className="text-blue-600 hover:underline">
                      Avaliar
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Evolução do Risco */}
        <section className="bg-white border border-gray-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Evolução da Taxa de Risco</h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={evolutionData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="window" />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, "Taxa"]} />
                <Line type="monotone" dataKey="flaggedPct" stroke="#dc2626" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Como a proporção de alunos em risco varia ao longo do semestre.
          </p>
        </section>
      </div>

      {/* 3. DISTRIBUIÇÃO E FEATURES */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2">
          <h2 className="text-lg font-semibold mb-2">Distribuição de Scores de Risco</h2>
          <div className="bg-white border border-gray-200 rounded-lg p-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.risk_bins}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="bin_start" tickFormatter={(v) => v.toFixed(1)} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#dc2626" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2">Fatores de Risco Dominantes</h2>
          <div className="bg-white border border-gray-200 rounded-lg p-4 h-64 overflow-y-auto">
            <ul className="space-y-3">
              {stats.top_features.map((f, i) => (
                <li key={f.feature} className="flex items-center gap-3">
                  <span className="w-6 text-xs font-bold text-gray-400">#{i + 1}</span>
                  <span className="w-24 font-mono text-xs">{f.feature}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-gray-900 h-2 rounded-full"
                      style={{ width: `${(f.mean_abs_shap / stats.top_features[0].mean_abs_shap) * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}