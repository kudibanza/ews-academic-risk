import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, CheckCircle2, MessageSquare, ShieldCheck } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";

// DICIONÁRIO DE TRADUÇÃO DE FEATURES
const FEATURE_METADATA: Record<string, { label: string; description: string }> = {
  S_vle: {
    label: "[S_vle] Volume de Acessos",
    description: "Quantidade total de cliques e interações na plataforma (VLE).",
  },
  D_active: {
    label: "[D_active] Dias Ativos",
    description: "Número de dias distintos em que o aluno acedeu à plataforma.",
  },
  H_entropy: {
    label: "[H_entropy] Diversidade de Estudo",
    description: "Variedade de recursos consultados (ex: ler fóruns, ver vídeos, ler PDFs).",
  },
  Delta_t: {
    label: "[Delta_t] Latência de Submissão",
    description: "Média de dias de atraso na entrega de trabalhos (valores negativos = entregou antes do prazo).",
  },
  S_score: {
    label: "[S_score] Média de Notas",
    description: "Média das classificações obtidas nas avaliações até ao momento.",
  },
  click_trend: {
    label: "[click_trend] Tendência de Atividade",
    description: "Variação de cliques nas últimas semanas (positivo = a aumentar, negativo = a diminuir).",
  },
};

export function RiskCardPage() {
  const { studentId, window } = useParams<{ studentId: string; window: string }>();
  const id = Number(studentId);

  const cardQuery = useQuery({
    queryKey: ["card", id, window],
    queryFn: () => api.riskCard(id, window!),
    enabled: !!id && !!window,
  });

  if (cardQuery.isLoading) return <p>Loading…</p>;
  if (cardQuery.isError || !cardQuery.data) return <p className="text-red-600">Card not found.</p>;

  const card = cardQuery.data;
  
  const riskPercentage = Math.round(card.risk_score * 100);
  const isHighRisk = riskPercentage > 70;
  const isMediumRisk = riskPercentage > 40 && riskPercentage <= 70;

  // Função para formatar valores e dar-lhes contexto
  const formatValueWithContext = (feature: string, val: number | string | null) => {
    if (val === null) return "N/A";
    const numVal = Number(val);
    if (isNaN(numVal)) return String(val);

    let formatted = Number.isInteger(numVal) ? numVal.toString() : numVal.toFixed(2);
    
    // Adicionar contexto simples
    if (feature === "Delta_t") {
      return numVal > 0 ? `${formatted} dias (Atrasado)` : `${Math.abs(numVal)} dias (Adiantado)`;
    }
    if (feature === "S_score") {
      return `${formatted} / 100 (${numVal < 50 ? 'Abaixo da média' : 'Bom'})`;
    }
    if (feature === "click_trend") {
      return numVal > 0 ? `+${formatted} (A subir)` : `${formatted} (A descer)`;
    }
    
    return formatted;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      <div className="flex justify-between items-center">
        <Link to="/" className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" /> Voltar à lista
        </Link>
        <Link 
          to="/scs" 
          className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-100 transition-colors"
        >
          <MessageSquare className="w-4 h-4" /> Evaluate Explanation (SCS)
        </Link>
      </div>

      {/* CABEÇALHO */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Aluno {card.student_id}</h1>
            <p className="text-sm text-gray-500">Apresentação: {card.presentation} • Janela: {card.window}</p>
          </div>
          <div className={`px-4 py-2 rounded-lg font-bold text-sm ${
            card.flagged ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"
          }`}>
            {card.flagged ? "Requer Intervenção" : "Risco Aceitável"}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm font-medium">
            <span>Probabilidade de Falha/Abandono</span>
            <span className="text-lg font-bold">{riskPercentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div 
              className={`h-4 rounded-full ${isHighRisk ? 'bg-red-600' : isMediumRisk ? 'bg-yellow-500' : 'bg-green-500'}`}
              style={{ width: `${riskPercentage}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 text-right mt-1">
            Limite de alerta do sistema: {Math.round(card.threshold_applied * 100)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* FATORES DE RISCO */}
        <div className="bg-white border border-red-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4 text-red-700">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="font-bold">Fatores de Risco (Aumentam)</h3>
          </div>
          {card.top_positive_factors.length > 0 ? (
            <ul className="space-y-5">
              {card.top_positive_factors.map((f) => {
                const meta = FEATURE_METADATA[f.feature] || { label: f.feature, description: "" };
                return (
                  <li key={f.feature} className="flex flex-col border-b border-gray-100 last:border-0 pb-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="font-semibold text-gray-900">{meta.label}</span>
                        {meta.description && (
                          <p className="text-xs text-gray-500 mt-0.5 max-w-[200px] leading-tight">
                            {meta.description}
                          </p>
                        )}
                      </div>
                      <span className="font-bold text-red-600 bg-red-50 px-2 py-1 rounded text-sm whitespace-nowrap">
                        +{f.shap_value.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-2 text-xs font-medium text-gray-700 bg-gray-50 p-2 rounded">
                      Valor do aluno: {formatValueWithContext(f.feature, f.feature_value)}
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 italic">Nenhum fator de risco significativo.</p>
          )}
        </div>

        {/* FATORES PROTETORES */}
        <div className="bg-white border border-green-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4 text-green-700">
            <ShieldCheck className="w-5 h-5" />
            <h3 className="font-bold">Fatores Protetores (Reduzem)</h3>
          </div>
          {card.top_negative_factors.length > 0 ? (
            <ul className="space-y-5">
              {card.top_negative_factors.map((f) => {
                const meta = FEATURE_METADATA[f.feature] || { label: f.feature, description: "" };
                return (
                  <li key={f.feature} className="flex flex-col border-b border-gray-100 last:border-0 pb-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="font-semibold text-gray-900">{meta.label}</span>
                        {meta.description && (
                          <p className="text-xs text-gray-500 mt-0.5 max-w-[200px] leading-tight">
                            {meta.description}
                          </p>
                        )}
                      </div>
                      <span className="font-bold text-green-600 bg-green-50 px-2 py-1 rounded text-sm whitespace-nowrap">
                        {f.shap_value.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-2 text-xs font-medium text-gray-700 bg-gray-50 p-2 rounded">
                      Valor do aluno: {formatValueWithContext(f.feature, f.feature_value)}
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 py-6">
              <ShieldCheck className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm">Nenhum fator protetor identificado.</p>
            </div>
          )}
        </div>
      </div>

      {/* PLANO DE AÇÃO */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
        <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-blue-600" />
          Plano de Ação Sugerido
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Com base no perfil do aluno, o sistema sugere agendar uma reunião de acompanhamento.
        </p>
        <div className="flex gap-3">
          <button className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-gray-800 transition-colors">
            Agendar Reunião
          </button>
          <button className="bg-white border border-gray-300 text-gray-700 rounded-lg px-4 py-2 text-sm font-medium hover:bg-gray-50 transition-colors">
            Enviar Email de Alerta
          </button>
        </div>
      </div>
    </div>
  );
}