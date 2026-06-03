"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Save, Trash2 } from "lucide-react";
import { NavShell } from "@/components/NavShell";
import { apiFetch, formatHours, progressPercent, remainingPercent, Subject } from "@/lib/api";

type Drafts = Record<number, string>;

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [requiredHours, setRequiredHours] = useState<Drafts>({});
  const [savingId, setSavingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      const subjectList = await apiFetch<Subject[]>("/subjects");
      setSubjects(subjectList);
      setRequiredHours(Object.fromEntries(subjectList.map((subject) => [subject.id, String(subject.required_hours)])));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load subjects");
    }
  }

  async function saveRequiredHours(subject: Subject) {
    const hours = Number(requiredHours[subject.id] ?? subject.required_hours);
    if (!Number.isFinite(hours) || hours <= 0) {
      setError("必要時間は0より大きい時間で入力してください");
      return;
    }

    setError("");
    setSavingId(subject.id);
    try {
      await apiFetch<Subject>(`/subjects/${subject.id}`, {
        method: "PATCH",
        body: { required_hours: hours },
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update subject");
    } finally {
      setSavingId(null);
    }
  }

  async function remove(id: number) {
    await apiFetch<void>(`/subjects/${id}`, { method: "DELETE" });
    await load();
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <NavShell>
      <section className="stack">
        <div className="row">
          <div>
            <p className="eyebrow">Subjects</p>
            <h1>科目一覧</h1>
          </div>
          <Link className="button" href="/subjects/new">
            <Plus size={17} />
            科目追加
          </Link>
        </div>
        {error ? <p className="error">{error}</p> : null}
        <div className="grid grid-2">
          {subjects.map((subject) => {
            const percent = progressPercent(subject);
            const remaining = remainingPercent(subject);
            return (
              <article className="card stack" key={subject.id}>
                <div className="row">
                  <div>
                    <h2>{subject.name}</h2>
                    <p>締切 {subject.deadline_date}</p>
                  </div>
                  <span className={subject.status === "completed" ? "badge ok" : "badge warn"}>
                    {subject.status}
                  </span>
                </div>
                <div className="progress">
                  <span style={{ width: `${percent}%` }} />
                </div>
                <p>
                  完了 {formatHours(subject.completed_hours)} / 必要 {formatHours(subject.required_hours)} / 残り {remaining}%
                </p>
                <div className="time-edit">
                  <div className="field">
                    <label htmlFor={`required-${subject.id}`}>必要時間(時間)</label>
                    <input
                      id={`required-${subject.id}`}
                      type="number"
                      min="0.01"
                      max="10000"
                      step="0.25"
                      value={requiredHours[subject.id] ?? String(subject.required_hours)}
                      onChange={(event) =>
                        setRequiredHours((current) => ({
                          ...current,
                          [subject.id]: event.target.value,
                        }))
                      }
                    />
                  </div>
                  <button
                    className="button secondary"
                    disabled={savingId === subject.id}
                    type="button"
                    onClick={() => void saveRequiredHours(subject)}
                  >
                    <Save size={17} />
                    {savingId === subject.id ? "保存中" : "保存"}
                  </button>
                </div>
                <button className="ghost-button" type="button" onClick={() => void remove(subject.id)}>
                  <Trash2 size={17} />
                  削除
                </button>
              </article>
            );
          })}
        </div>
      </section>
    </NavShell>
  );
}
