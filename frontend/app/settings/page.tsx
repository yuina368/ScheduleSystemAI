"use client";

import { FormEvent, useEffect, useState } from "react";
import { NavShell } from "@/components/NavShell";
import { apiFetch, StudySetting } from "@/lib/api";

export default function SettingsPage() {
  const [hours, setHours] = useState("2");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const setting = await apiFetch<StudySetting>("/settings/study-time");
        setHours(String(setting.daily_available_hours));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load settings");
      }
    }
    void load();
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await apiFetch<StudySetting>("/settings/study-time", {
        method: "POST",
        body: { daily_available_hours: Number(hours) },
      });
      setMessage("保存しました。今日以降の計画を再計算しました。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    }
  }

  return (
    <NavShell>
      <form className="panel stack" onSubmit={submit}>
        <div>
          <p className="eyebrow">Study Time</p>
          <h1>1日の学習可能時間</h1>
          <p>この時間を基準に、今日の予定が多すぎるかを判定します。</p>
        </div>
        <div className="field">
          <label htmlFor="hours">学習可能時間</label>
          <input
            id="hours"
            type="number"
            min="0.25"
            max="24"
            step="0.25"
            value={hours}
            onChange={(event) => setHours(event.target.value)}
            required
          />
        </div>
        {error ? <p className="error">{error}</p> : null}
        {message ? <p className="success">{message}</p> : null}
        <button className="button" type="submit">
          保存する
        </button>
      </form>
    </NavShell>
  );
}
