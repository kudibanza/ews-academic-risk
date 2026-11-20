import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export function SCSPage() {
  const questionsQuery = useQuery({ queryKey: ["scs"], queryFn: api.scsQuestions });
  const [responses, setResponses] = useState<Record<number, number>>({});
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      api.scsSubmit(
        Object.entries(responses).map(([id, score]) => ({
          id: Number(id),
          score,
        }))
      ),
    onSuccess: () => setSubmitted(true),
  });

  if (questionsQuery.isLoading) return <p>Loading…</p>;
  if (questionsQuery.isError || !questionsQuery.data) return <p className="text-red-600">Failed to load.</p>;

  if (submitted) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <h1 className="text-xl font-semibold text-green-700 mb-2">Thank you</h1>
        <p className="text-sm text-green-700">Your responses have been recorded.</p>
        
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">System Causability Scale</h1>
       <Link to="/" className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" /> Voltar à lista
        </Link>
      <p className="text-sm text-gray-600">
        Rate each statement from 1 (strongly disagree) to 5 (strongly agree).
      </p>
      {questionsQuery.data.map((q) => (
        <div key={q.id} className="bg-white border border-gray-200 rounded p-4">
          <p className="text-sm mb-2">{q.id}. {q.text}</p>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((v) => (
              <button
                key={v}
                onClick={() => setResponses((r) => ({ ...r, [q.id]: v }))}
                className={`w-9 h-9 rounded border text-sm ${
                  responses[q.id] === v
                    ? "bg-gray-900 text-white border-gray-900"
                    : "bg-white border-gray-300 hover:border-gray-400"
                }`}
              >
                {v}
              </button>
            ))}
          </div>
        </div>
      ))}
      <button
        onClick={() => mutation.mutate()}
        disabled={Object.keys(responses).length !== questionsQuery.data.length || mutation.isPending}
        className="bg-gray-900 text-white rounded px-4 py-2 text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
      >
        {mutation.isPending ? "Submitting…" : "Submit"}
      </button>
    </div>
  );
}