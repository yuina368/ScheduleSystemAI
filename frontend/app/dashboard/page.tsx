"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, Plus } from "lucide-react";
import { NavShell } from "@/components/NavShell";
import { PomodoroTimer } from "@/components/PomodoroTimer";
import { apiFetch, formatHours, PlanSummary, progressPercent, Subject } from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<PlanSummary | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [today, subjectList] = await Promise.all([
        apiFetch<PlanSummary>("/plans/today"),
        apiFetch<Subject[]>("/subjects"),
      ]);
      setSummary(today);
      setSubjects(subjectList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <NavShell>
      <div className="split">
        <section className="stack">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h1>今日の学習計画</h1>
          </div>
          {error ? <p className="error">{error}</p> : null}
          {summary ? (
            <div className="grid grid-3">
              <div className="card metric">
                <span className="muted">今日の予定</span>
                <strong>{formatHours(summary.total_planned_hours)}</strong>
              </div>
              <div className="card metric">
                <span className="muted">学習可能時間</span>
                <strong>{formatHours(summary.daily_available_hours)}</strong>
              </div>
              <div className="card metric">
                <span className="muted">状態</span>
                <strong>{summary.over_capacity ? "要調整" : "順調"}</strong>
              </div>
            </div>
          ) : null}
          {summary?.over_capacity ? (
            <div className="card row">
              <div>
                <h3>今日の予定が学習可能時間を超えています</h3>
                <p>締切が近い科目の必要時間が多くなっています。学習可能時間か科目条件を見直せます。</p>
              </div>
              <AlertTriangle color="#a15c06" />
            </div>
          ) : null}
          <div className="panel stack">
            <div className="row">
              <h2>今日やる科目</h2>
              <Link href="/checkin" className="button">
                <CheckCircle2 size={17} />
                入力
              </Link>
            </div>
            <div className="list">
              {summary?.plans.length ? (
                summary.plans.map((plan) => (
                  <div className="card row" key={plan.id}>
                    <div>
                      <h3>{plan.subject.name}</h3>
                      <p>
                        締切 {plan.subject.deadline_date} / 予定 {formatHours(plan.planned_hours)}
                      </p>
                    </div>
                    <span className="badge ok">Today</span>
                  </div>
                ))
              ) : (
                <p>今日の計画はまだありません。科目と学習時間を登録してください。</p>
              )}
            </div>
          </div>
        </section>
        <aside className="stack">
          <PomodoroTimer />
          <div className="panel stack">
            <div className="row">
              <h2>科目</h2>
              <Link href="/subjects/new" className="button secondary">
                <Plus size={17} />
                追加
              </Link>
            </div>
            <div className="list">
              {subjects.length ? (
                subjects.slice(0, 5).map((subject) => {
                  const percent = progressPercent(subject);
                  return (
                    <div className="card stack" key={subject.id}>
                      <div className="row">
                        <h3>{subject.name}</h3>
                        <span className={subject.status === "completed" ? "badge ok" : "badge warn"}>
                          {subject.status}
                        </span>
                      </div>
                      <div className="progress" aria-label={`${subject.name} progress`}>
                        <span style={{ width: `${percent}%` }} />
                      </div>
                      <p>
                        {formatHours(subject.completed_hours)} / {formatHours(subject.required_hours)}
                      </p>
                    </div>
                  );
                })
              ) : (
                <p>科目が未登録です。</p>
              )}
            </div>
          </div>
        </aside>
      </div>
    </NavShell>
  );
}
