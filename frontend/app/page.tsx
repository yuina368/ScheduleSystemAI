import Link from "next/link";

export default function Home() {
  return (
    <main className="auth-page">
      <section className="auth-panel stack">
        <div>
          <p className="eyebrow">ScheduleSystemAI</p>
          <h1>今日の学習量を、毎日組み直す。</h1>
          <p>科目、締切、学習可能時間を登録すると、残り時間を日割りして学習計画を作成します。</p>
        </div>
        <div className="grid grid-2">
          <Link className="button" href="/signup">
            新規登録
          </Link>
          <Link className="button secondary" href="/login">
            ログイン
          </Link>
        </div>
      </section>
    </main>
  );
}
