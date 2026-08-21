import { api } from "./client";

export interface User {
  id: string;
  username: string;
  role: string;
  created_at: string;
}

interface AuthResponse {
  user: User;
}

export async function login(username: string, password: string): Promise<User> {
  const res = await api.post<AuthResponse>("/auth/login", { username, password });
  return res.user;
}

export async function register(username: string, password: string): Promise<User> {
  const res = await api.post<AuthResponse>("/auth/register", { username, password });
  return res.user;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}

export async function me(): Promise<User> {
  return api.get<User>("/auth/me");
}