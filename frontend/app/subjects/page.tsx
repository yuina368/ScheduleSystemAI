"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Trash2 } from "lucide-react";
import { NavShell } from "@/components/NavShell";
import { apiFetch, formatHours, progressPercent, Subject } from "@/lib/api";

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      setSubjects(await apiFetch<Subject[]>("/subjects"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load subjects");
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
                  完了 {formatHours(subject.completed_hours)} / 必要 {formatHours(subject.required_hours)}
                </p>
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
