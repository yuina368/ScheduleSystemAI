"use client";

import { useEffect, useState } from "react";
import { NavShell } from "@/components/NavShell";
import { apiFetch, formatHours, hoursToMinutes, PlanSummary } from "@/lib/api";

type Drafts = Record<number, string>;

export default function CheckinPage() {
  const [summary, setSummary] = useState<PlanSummary | null>(null);
  const [drafts, setDrafts] = useState<Drafts>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const today = await apiFetch<PlanSummary>("/plans/today");
    setSummary(today);
    setDrafts(Object.fromEntries(today.plans.map((plan) => [plan.subject_id, String(hoursToMinutes(plan.planned_hours))])));
  }

  async function submit(subjectId: number, didStudy: boolean) {
    setError("");
    setMessage("");
    try {
      await apiFetch("/study-logs", {
        method: "POST",
        body: {
          subject_id: subjectId,
          actual_hours: didStudy ? Number(drafts[subjectId] ?? 0) / 60 : 0,
          did_study: didStudy,
        },
      });
      await load();
      setMessage("記録しました。今日以降の計画を再計算しました。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save check-in");
    }
  }

  useEffect(() => {
    void load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load plan"));
  }, []);

  return (
    <NavShell>
      <section className="stack">
        <div>
          <p className="eyebrow">Check-in</p>
          <h1>今日の実績入力</h1>
          <p>やった時間を入力すると、残りの日程が自動で再計算されます。</p>
        </div>
        {error ? <p className="error">{error}</p> : null}
        {message ? <p className="success">{message}</p> : null}
        <div className="list">
          {summary?.plans.length ? (
            summary.plans.map((plan) => (
              <article className="card stack" key={plan.id}>
                <div className="row">
                  <div>
                    <h2>{plan.subject.name}</h2>
                    <p>今日の予定 {formatHours(plan.planned_hours)}</p>
                  </div>
                  <span className="badge ok">{plan.subject.deadline_date}</span>
                </div>
                <div className="field">
                  <label htmlFor={`actual-${plan.subject_id}`}>実際にやった時間(分)</label>
                  <input
                    id={`actual-${plan.subject_id}`}
                    type="number"
                    min="0"
                    max="1440"
                    step="1"
                    value={drafts[plan.subject_id] ?? "0"}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [plan.subject_id]: event.target.value,
                      }))
                    }
                  />
                </div>
                <div className="grid grid-2">
                  <button className="button" type="button" onClick={() => void submit(plan.subject_id, true)}>
                    やった
                  </button>
                  <button
                    className="button warning"
                    type="button"
                    onClick={() => void submit(plan.subject_id, false)}
                  >
                    やってない
                  </button>
                </div>
              </article>
            ))
          ) : (
            <div className="panel">
              <p>今日入力できる計画がありません。</p>
            </div>
          )}
        </div>
      </section>
    </NavShell>
  );
}
