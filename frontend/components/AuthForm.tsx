"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, AuthResponse, setToken } from "@/lib/api";

type Props = {
  mode: "login" | "signup";
};

export function AuthForm({ mode }: Props) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiFetch<AuthResponse>(`/auth/${mode}`, {
        method: "POST",
        auth: false,
        body: { email, password },
      });
      setToken(data.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  const isSignup = mode === "signup";

  return (
    <div className="auth-page">
      <form className="auth-panel stack" onSubmit={submit}>
        <div>
          <p className="eyebrow">{isSignup ? "新規登録" : "ログイン"}</p>
          <h1>{isSignup ? "学習計画を始める" : "学習計画に戻る"}</h1>
          <p>科目と締切、1日の学習可能時間から、今日やるべき学習量を自動で再計算します。</p>
        </div>
        <div className="field">
          <label htmlFor="email">メールアドレス</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="password">パスワード</label>
          <input
            id="password"
            type="password"
            autoComplete={isSignup ? "new-password" : "current-password"}
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="button full" disabled={loading} type="submit">
          {loading ? "送信中..." : isSignup ? "登録する" : "ログインする"}
        </button>
        <p>
          {isSignup ? "すでにアカウントがありますか？ " : "アカウントが未作成ですか？ "}
          <Link href={isSignup ? "/login" : "/signup"} className="success">
            {isSignup ? "ログインへ" : "新規登録へ"}
          </Link>
        </p>
      </form>
    </div>
  );
}
