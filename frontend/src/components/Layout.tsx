import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

export function Layout() {
  const { logout, role, username } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-semibold text-lg">
          <img src="/logo-ews.png" alt="EWS logo" className="h-8 w-8 object-contain" />
          <span>EWS — Early Warning System</span>
        </Link>
        <div className="flex items-center gap-4 text-sm">
          {role === "admin" && (
            <>
              <Link to="/admin" className="text-gray-700 hover:text-gray-900">
                Dashboard
              </Link>
              <Link to="/" className="text-gray-700 hover:text-gray-900">
                Students
              </Link>
              <Link to="/admin/users" className="text-gray-700 hover:text-gray-900">
                Users
              </Link>
            </>
          )}
          <span className="text-gray-500">
            {username} ({role})
          </span>
          <button
            onClick={handleLogout}
            className="text-gray-600 hover:text-gray-900"
          >
            Logout
          </button>
        </div>
      </header>
      <main className="flex-1 p-6 max-w-6xl mx-auto w-full">
        <Outlet />
      </main>
    </div>
  );
}