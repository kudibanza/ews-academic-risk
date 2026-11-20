import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { AdminRoute } from "./components/AdminRoute";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { RiskCardPage } from "./pages/RiskCardPage";
import { RiskListPage } from "./pages/RiskListPage";
import { SCSPage } from "./pages/SCSPage";
import { UserManagementPage } from "./pages/userManagementPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route index element={<RiskListPage />} />
                <Route path="students/:studentId/:window" element={<RiskCardPage />} />
                <Route path="scs" element={<SCSPage />} />
                <Route element={<AdminRoute />}>
                  <Route path="admin" element={<AdminDashboardPage />} />
                  <Route path="admin/users" element={<UserManagementPage />} />
                </Route>
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}