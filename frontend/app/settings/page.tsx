"use client";

import { FormEvent, useEffect, useState } from "react";
import { NavShell } from "@/components/NavShell";
import { apiFetch, StudySetting } from "@/lib/api";

export default function SettingsPage() {
  const [weekdayHours, setWeekdayHours] = useState("2");
  const [weekendHours, setWeekendHours] = useState("2");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [maxDailySubjects, setMaxDailySubjects] = useState("3");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const setting = await apiFetch<StudySetting>("/settings/study-time");
        setWeekdayHours(String(setting.weekday_available_hours ?? setting.daily_available_hours));
        setWeekendHours(String(setting.weekend_available_hours ?? setting.daily_available_hours));
        setWebhookUrl(setting.morning_webhook_url ?? "");
        setMaxDailySubjects(String(setting.max_daily_subjects ?? 3));
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
          morning_webhook_url: webhookUrl.trim() || null,
          max_daily_subjects: Number(maxDailySubjects),
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
          <p>平日・土日の予定配分と、毎朝の学習ブリーフィングを設定します。</p>
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
        <div className="field">
          <label htmlFor="max-daily-subjects">一日の最大科目数</label>
          <input
            id="max-daily-subjects"
            type="number"
            min="1"
            max="12"
            step="1"
            value={maxDailySubjects}
            onChange={(event) => setMaxDailySubjects(event.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="webhook-url">毎朝通知 Webhook URL</label>
          <input
            id="webhook-url"
            type="url"
            placeholder="https://example.com/webhook"
            value={webhookUrl}
            onChange={(event) => setWebhookUrl(event.target.value)}
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
