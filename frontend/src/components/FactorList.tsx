import type { Factor } from "../api/types";

export function FactorList({
  title,
  factors,
  color,
}: {
  title: string;
  factors: Factor[];
  color: "red" | "green";
}) {
  const bg = color === "red" ? "bg-red-50 border-red-200" : "bg-green-50 border-green-200";
  const text = color === "red" ? "text-red-700" : "text-green-700";
  return (
    <div className={`rounded-lg border p-4 ${bg}`}>
      <h3 className={`font-semibold mb-2 ${text}`}>{title}</h3>
      <ul className="space-y-2 text-sm">
        {factors.map((f) => (
          <li key={f.feature} className="flex justify-between">
            <span>
              <span className="font-mono">{f.feature}</span>
              {f.feature_value !== null && (
                <span className="text-gray-500 ml-2">= {String(f.feature_value)}</span>
              )}
            </span>
            <span className={text}>{f.shap_value.toFixed(3)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}