"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, AlertTriangle, BrainCircuit, CheckCircle2, Plus, TrendingUp } from "lucide-react";
import { NavShell } from "@/components/NavShell";
import { PomodoroTimer } from "@/components/PomodoroTimer";
import {
  apiFetch,
  formatHours,
  formatPercent,
  PlanSummary,
  progressPercent,
  RegressionAnalysis,
  remainingPercent,
  Subject,
} from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<PlanSummary | null>(null);
  const [analysis, setAnalysis] = useState<RegressionAnalysis | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const [today, subjectList, regression] = await Promise.all([
        apiFetch<PlanSummary>("/plans/today"),
        apiFetch<Subject[]>("/subjects"),
        apiFetch<RegressionAnalysis>("/analytics/study-regression"),
      ]);
      setSummary(today);
      setSubjects(subjectList);
      setAnalysis(regression);
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
            <div className="grid dashboard-metrics">
              <div className="card metric">
                <span className="muted">今日の予定</span>
                <strong>{formatHours(summary.total_planned_hours)}</strong>
              </div>
              <div className="card metric">
                <span className="muted">学習可能時間</span>
                <strong>{formatHours(summary.daily_available_hours)}</strong>
              </div>
              <div className="card metric">
                <span className="muted">今日の科目数</span>
                <strong>
                  {summary.plans.length}/{summary.max_daily_subjects}
                </strong>
              </div>
              {analysis ? (
                <div className="card metric streak-metric">
                  <span className="muted">連続学習</span>
                  <strong>
                    <span aria-hidden="true">🔥</span>
                    {analysis.study_streak_days}日連続
                  </strong>
                </div>
              ) : null}
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
          {analysis ? (
            <div className="panel ai-panel stack">
              <div className="row">
                <div>
                  <p className="eyebrow">Completion AI</p>
                  <h2>最終達成確率</h2>
                </div>
                <BrainCircuit color="#29437a" />
              </div>
              <div className="grid grid-3">
                <div className="analysis-metric">
                  <span className="muted">最終達成確率</span>
                  <strong>{formatPercent(analysis.final_completion_probability)}</strong>
                </div>
                <div className="analysis-metric">
                  <span className="muted">残り必要時間</span>
                  <strong>{formatHours(analysis.total_remaining_hours)}</strong>
                </div>
                <div className="analysis-metric">
                  <span className="muted">信頼度</span>
                  <strong>{formatPercent(analysis.confidence)}</strong>
                </div>
              </div>
              <div className="insight-band">
                <span className="ai-chip">
                  <Activity size={14} />
                  {analysis.final_status_label}
                </span>
                <span>
                  <TrendingUp size={14} />
                  直近実行率 {formatPercent(analysis.recent_execution_rate)}
                </span>
                <span>予測可能学習 {formatHours(analysis.projected_study_hours)}</span>
                <span>予測完了率 {formatPercent(analysis.projected_completion_rate)}</span>
              </div>
              <div className="daily-history">
                <div className="daily-row forecast-head">
                  <span>科目</span>
                  <span>締切</span>
                  <span>残り</span>
                  <span>確率</span>
                </div>
                {analysis.subject_forecasts.slice(0, 5).map((forecast) => (
                  <div className="daily-row" key={forecast.subject_id}>
                    <span>{forecast.subject_name}</span>
                    <span>{forecast.deadline_date}</span>
                    <span>{formatHours(forecast.remaining_hours)}</span>
                    <strong>{formatPercent(forecast.final_completion_probability)}</strong>
                  </div>
                ))}
              </div>
              <div className="daily-history">
                <div className="daily-row daily-head">
                  <span>日付</span>
                  <span>予定</span>
                  <span>実績</span>
                  <span>達成率</span>
                </div>
                {analysis.daily_summaries
                  .slice()
                  .reverse()
                  .slice(0, 3)
                  .map((daily) => (
                    <div className="daily-row" key={daily.log_date}>
                      <span>{daily.log_date}</span>
                      <span>{formatHours(daily.planned_hours)}</span>
                      <span>{formatHours(daily.actual_hours)}</span>
                      <strong>{formatPercent(daily.achievement_rate)}</strong>
                    </div>
                  ))}
              </div>
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
                      {plan.priority_reasons ? (
                        <div className="reason-list">
                          {plan.priority_reasons.split("、").map((reason) => (
                            <span className="reason-chip" key={`${plan.id}-${reason}`}>
                              {reason}
                            </span>
                          ))}
                          {plan.priority_score ? (
                            <span className="reason-chip score">score {Math.round(plan.priority_score)}</span>
                          ) : null}
                        </div>
                      ) : null}
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
          <PomodoroTimer studyHours={summary?.daily_available_hours} />
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
                  const remaining = remainingPercent(subject);
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
                        {formatHours(subject.completed_hours)} / {formatHours(subject.required_hours)} / 残り {remaining}%
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
