"use client";

import { Pause, Play, RotateCcw, SkipForward } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { formatHours } from "@/lib/api";

const STUDY_SECONDS = 15 * 60;
const BREAK_SECONDS = 5 * 60;

type PomodoroMode = "study" | "break";

type Props = {
  studyHours?: number;
};

function formatTimer(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

export function PomodoroTimer({ studyHours }: Props) {
  const [mode, setMode] = useState<PomodoroMode>("study");
  const [secondsLeft, setSecondsLeft] = useState(STUDY_SECONDS);
  const [running, setRunning] = useState(false);
  const totalSeconds = mode === "study" ? STUDY_SECONDS : BREAK_SECONDS;
  const progress = useMemo(() => ((totalSeconds - secondsLeft) / totalSeconds) * 100, [secondsLeft, totalSeconds]);
  const studyMinutes = typeof studyHours === "number" ? Math.max(0, Math.round(studyHours * 60)) : null;
  const sessionCount = studyMinutes === null ? null : Math.ceil(studyMinutes / 15);

  function switchMode(nextMode: PomodoroMode) {
    setMode(nextMode);
    setSecondsLeft(nextMode === "study" ? STUDY_SECONDS : BREAK_SECONDS);
    setRunning(false);
  }

  function nextSession() {
    switchMode(mode === "study" ? "break" : "study");
  }

  function resetSession() {
    setSecondsLeft(totalSeconds);
    setRunning(false);
  }

  useEffect(() => {
    if (!running) return;

    const timer = window.setInterval(() => {
      setSecondsLeft((current) => Math.max(0, current - 1));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [running]);

  useEffect(() => {
    if (!running || secondsLeft > 0) return;

    const nextMode = mode === "study" ? "break" : "study";
    setMode(nextMode);
    setSecondsLeft(nextMode === "study" ? STUDY_SECONDS : BREAK_SECONDS);
    setRunning(false);
  }, [mode, running, secondsLeft]);

  return (
    <section className="panel stack pomodoro" aria-label="ポモドーロタイマー">
      <div className="row">
        <div>
          <p className="eyebrow">Pomodoro</p>
          <h2>ポモドーロタイマー</h2>
        </div>
        <span className={mode === "study" ? "badge ok" : "badge warn"}>{mode === "study" ? "学習15分" : "休憩5分"}</span>
      </div>
      <div className="timer-display" aria-live="polite">
        {formatTimer(secondsLeft)}
      </div>
      <div className="timer-target">
        {studyMinutes === null ? (
          <p>1日の勉強時間を読み込むと、必要な15分タイマーの回数を表示します。</p>
        ) : (
          <>
            <span className="muted">1日の勉強時間 {formatHours(studyHours ?? 0)}</span>
            <strong>{sessionCount}回</strong>
            <p>15分タイマーを{sessionCount}回回すと達成できます。</p>
          </>
        )}
      </div>
      <div className="progress timer-progress" aria-hidden="true">
        <span style={{ width: `${progress}%` }} />
      </div>
      <div className="timer-controls">
        <button
          className="button"
          type="button"
          onClick={() => setRunning((current) => !current)}
          aria-label={running ? "一時停止" : "開始"}
          title={running ? "一時停止" : "開始"}
        >
          {running ? <Pause size={18} /> : <Play size={18} />}
        </button>
        <button className="ghost-button" type="button" onClick={resetSession} aria-label="リセット" title="リセット">
          <RotateCcw size={18} />
        </button>
        <button className="ghost-button" type="button" onClick={nextSession} aria-label="次へ" title="次へ">
          <SkipForward size={18} />
        </button>
      </div>
    </section>
  );
}
