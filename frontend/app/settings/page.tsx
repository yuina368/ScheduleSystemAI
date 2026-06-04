"use client";

import { FormEvent, useEffect, useState } from "react";
import { NavShell } from "@/components/NavShell";
import { apiFetch, StudySetting } from "@/lib/api";

export default function SettingsPage() {
  const [weekdayHours, setWeekdayHours] = useState("2");
  const [weekendHours, setWeekendHours] = useState("2");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const setting = await apiFetch<StudySetting>("/settings/study-time");
        setWeekdayHours(String(setting.weekday_available_hours ?? setting.daily_available_hours));
        setWeekendHours(String(setting.weekend_available_hours ?? setting.daily_available_hours));
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
        body: {
          weekday_available_hours: Number(weekdayHours),
          weekend_available_hours: Number(weekendHours),
        },
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
        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="weekday-hours">平日の学習可能時間</label>
            <input
              id="weekday-hours"
              type="number"
              min="0.25"
              max="24"
              step="0.25"
              value={weekdayHours}
              onChange={(event) => setWeekdayHours(event.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="weekend-hours">土日の学習可能時間</label>
            <input
              id="weekend-hours"
              type="number"
              min="0.25"
              max="24"
              step="0.25"
              value={weekendHours}
              onChange={(event) => setWeekendHours(event.target.value)}
              required
            />
          </div>
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
