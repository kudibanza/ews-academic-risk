import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/admin");
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 w-full max-w-sm"
      >
          <div className="flex flex-col items-center mb-6">
            <img src="/logo-ews.png" alt="EWS logo" className="h-16 w-16 object-contain mb-3" />
            <h1 className="text-xl font-semibold">EWS — Early Warning System</h1>
            <p className="text-sm text-gray-500 mt-1">Sign in to continue</p>
          </div>
  {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
        <label className="block text-sm mb-1">Username</label>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full border border-gray-300 rounded px-3 py-2 mb-4"
          required
        />
        <label className="block text-sm mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-gray-300 rounded px-3 py-2 mb-6"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gray-900 text-white rounded py-2 font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <p className="text-xs text-xl text-gray-500 mt-4">
          <b>"Acting in the Present to Prevent the Future".</b> <br />
          This system is for authorized users only. Unauthorized access is prohibited.
        </p>
      </form>
    </div>
  );
}