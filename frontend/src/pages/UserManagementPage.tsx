import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { api } from "../api/client";

export function UserManagementPage() {
  const qc = useQueryClient();
  const usersQuery = useQuery({ queryKey: ["admin-users"], queryFn: api.admin.users });
  const [newUser, setNewUser] = useState({ username: "", password: "", role: "advisor" as "admin" | "advisor" });
  const [editingPasswordFor, setEditingPasswordFor] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState("");

  const createMutation = useMutation({
    mutationFn: () => api.admin.createUser(newUser.username, newUser.password, newUser.role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      setNewUser({ username: "", password: "", role: "advisor" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: { role?: "admin" | "advisor"; active?: boolean; password?: string } }) =>
      api.admin.updateUser(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      setEditingPasswordFor(null);
      setNewPassword("");
    },
  });

  function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!newUser.username || !newUser.password) return;
    createMutation.mutate();
  }

  function handlePasswordSubmit(e: FormEvent, userId: number) {
    e.preventDefault();
    if (newPassword.length < 6) return;
    updateMutation.mutate({ id: userId, patch: { password: newPassword } });
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">User Management</h1>

      <form onSubmit={handleCreate} className="bg-white border border-gray-200 rounded-lg p-4 flex gap-3 items-end">
        <div>
          <label className="block text-sm mb-1">Username</label>
          <input
            value={newUser.username}
            onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
            className="border border-gray-300 rounded px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Password</label>
          <input
            type="password"
            value={newUser.password}
            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
            className="border border-gray-300 rounded px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Role</label>
          <select
            value={newUser.role}
            onChange={(e) => setNewUser({ ...newUser, role: e.target.value as "admin" | "advisor" })}
            className="border border-gray-300 rounded px-3 py-2"
          >
            <option value="advisor">advisor</option>
            <option value="admin">admin</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="bg-gray-900 text-white rounded px-4 py-2 text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          Create user
        </button>
        {createMutation.isError && (
          <p className="text-red-600 text-sm">Failed to create user.</p>
        )}
      </form>

      {usersQuery.data && (
        <table className="w-full bg-white border border-gray-200 rounded">
          <thead className="bg-gray-100 text-left text-sm">
            <tr>
              <th className="px-4 py-2">ID</th>
              <th className="px-4 py-2">Username</th>
              <th className="px-4 py-2">Role</th>
              <th className="px-4 py-2">Active</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {usersQuery.data.map((u) => (
              <tr key={u.id} className="border-t border-gray-100 align-top">
                <td className="px-4 py-2">{u.id}</td>
                <td className="px-4 py-2 font-mono">{u.username}</td>
                <td className="px-4 py-2">
                  <select
                    value={u.role}
                    onChange={(e) => updateMutation.mutate({ id: u.id, patch: { role: e.target.value as "admin" | "advisor" } })}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    <option value="advisor">advisor</option>
                    <option value="admin">admin</option>
                  </select>
                </td>
                <td className="px-4 py-2">
                  <input
                    type="checkbox"
                    checked={u.active}
                    onChange={(e) => updateMutation.mutate({ id: u.id, patch: { active: e.target.checked } })}
                  />
                </td>
                <td className="px-4 py-2">
                  <div className="flex flex-col gap-2">
                    {u.active && (
                      <button
                        onClick={() => updateMutation.mutate({ id: u.id, patch: { active: false } })}
                        className="text-red-600 text-sm hover:underline text-left"
                      >
                        Deactivate
                      </button>
                    )}
                    {editingPasswordFor === u.id ? (
                      <form onSubmit={(e) => handlePasswordSubmit(e, u.id)} className="flex gap-2">
                        <input
                          type="password"
                          placeholder="New password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          className="border border-gray-300 rounded px-2 py-1 text-sm w-32"
                          required
                          minLength={6}
                        />
                        <button
                          type="submit"
                          className="bg-gray-900 text-white rounded px-2 py-1 text-xs hover:bg-gray-800"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => { setEditingPasswordFor(null); setNewPassword(""); }}
                          className="text-gray-600 text-xs hover:underline"
                        >
                          Cancel
                        </button>
                      </form>
                    ) : (
                      <button
                        onClick={() => { setEditingPasswordFor(u.id); setNewPassword(""); }}
                        className="text-gray-700 text-sm hover:underline text-left"
                      >
                        Change password
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}