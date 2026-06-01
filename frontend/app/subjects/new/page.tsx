"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { NavShell } from "@/components/NavShell";
import { apiFetch, Subject } from "@/lib/api";

export default function NewSubjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [deadlineDate, setDeadlineDate] = useState("");
  const [requiredHours, setRequiredHours] = useState("10");
  const [completedHours, setCompletedHours] = useState("0");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const nameValue = String(formData.get("name") || name);
    const deadlineValue = String(formData.get("deadline") || deadlineDate);
    const requiredValue = Number(formData.get("requiredHours") || requiredHours);
    const completedValue = Number(formData.get("completedHours") || completedHours);
    setError("");
    try {
      await apiFetch<Subject>("/subjects", {
        method: "POST",
        body: {
          name: nameValue,
          deadline_date: deadlineValue,
          required_hours: requiredValue,
          completed_hours: completedValue,
        },
      });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create subject");
    }
  }

  return (
    <NavShell>
      <form className="panel stack" onSubmit={submit}>
        <div>
          <p className="eyebrow">New Subject</p>
          <h1>科目登録</h1>
        </div>
        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="name">科目名</label>
            <input id="name" name="name" value={name} onChange={(event) => setName(event.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="deadline">締切日</label>
            <input
              id="deadline"
              name="deadline"
              type="date"
              value={deadlineDate}
              onChange={(event) => setDeadlineDate(event.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="requiredHours">必要学習時間</label>
            <input
              id="requiredHours"
              name="requiredHours"
              type="number"
              min="0.25"
              step="0.25"
              value={requiredHours}
              onChange={(event) => setRequiredHours(event.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="completedHours">完了済み時間</label>
            <input
              id="completedHours"
              name="completedHours"
              type="number"
              min="0"
              step="0.25"
              value={completedHours}
              onChange={(event) => setCompletedHours(event.target.value)}
            />
          </div>
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="button" type="submit">
          登録して計画を作る
        </button>
      </form>
    </NavShell>
  );
}
