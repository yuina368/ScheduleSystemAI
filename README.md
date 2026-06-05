# ScheduleSystemAI

![Version](https://img.shields.io/badge/version-v0.1.0-127267)
![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=nextdotjs)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-supported-4169E1?logo=postgresql&logoColor=white)
![Deploy](https://img.shields.io/badge/deploy-Vercel-black?logo=vercel)
![License](https://img.shields.io/badge/license-MIT-blue)

ScheduleSystemAI は、資格試験の学習における「今日どれくらい勉強すればよいか」を自動で割り出す学習時間配分アプリケーションです。

基本情報技術者試験や TOEIC のように、複数の科目・分野を期限までに進める必要がある学習で、ユーザーが毎日細かく計画を立て直さなくてもよい状態を目指しています。

公開 URL: https://schedule-system-ai.vercel.app/

## 開発背景

このアプリケーションは、資格試験の勉強における 1 日の勉強時間配分を支援するために作りました。

資格試験の学習では、次のような問題が起きやすいです。

- 今日はどの科目をどれくらいやるべきか判断するのが面倒
- 締切や試験日から逆算した学習量が見えにくい
- 予定より進んだ日・遅れた日のあとに計画を立て直すのが大変
- 「勉強する内容を決める」こと自体にエネルギーを使ってしまう

ScheduleSystemAI は、こうした負担を減らし、ユーザーができるだけ「非主体的」に資格試験の勉強へ入れるようにするためのアプリケーションです。

ここでの「非主体的」とは、学習そのものを放棄するという意味ではありません。毎日の学習配分や再計算をシステムに任せ、ユーザーは提示された計画に沿って勉強し、実績だけを入力するという意味です。

## コンセプト

```text
科目を登録する
  ↓
締切と必要時間から今日の学習時間を自動計算する
  ↓
ユーザーは今日やった分数を入力する
  ↓
残り時間と残り日数から計画を再計算する
```

このサイクルによって、学習計画を毎日手動で組み直す手間を減らします。

## 主な機能

- メールアドレスとパスワードによる新規登録・ログイン
- 科目登録
  - 科目名
  - 締切日
  - 必要学習時間
  - 完了済み時間
- 必要学習時間の編集
- 残り学習割合の表示
- 平日・土日の学習可能時間の設定
- 1 日に表示する最大科目数の設定
- 毎朝通知用 Webhook URL の保存
- 今日の学習計画の自動生成
- 締切・残り時間・達成率からの ML 風優先度スコアリング
- 学習実績の分単位入力
- 日別の予定時間・実績時間・達成率の保存と表示
- 日別実行率と残り必要時間を使った AI 風の最終達成確率予測
- 実績入力後の自動再計算
- 15 分学習 / 5 分休憩のポモドーロタイマー
- 1 日の学習時間から必要な 15 分タイマー回数を表示
- 今日の予定が学習可能時間を超えた場合の警告
- Vercel Cron による毎朝の学習ブリーフィング Webhook 送信

## 想定する利用シーン

- 基本情報技術者試験の科目別学習
- TOEIC のリスニング・リーディング対策
- 複数教材を期限までに進めたい資格試験学習
- 毎日の学習配分を自分で考える負担を減らしたいケース

## Web アプリケーション設計図

### 全体アーキテクチャ

```mermaid
flowchart LR
  User["User"]
  Frontend["Frontend\nNext.js / TypeScript\nVercel"]
  Backend["Backend\nFastAPI / SQLAlchemy\nVercel"]
  DB["PostgreSQL\nNeon / Supabase など"]

  User --> Frontend
  Frontend -->|"REST API"| Backend
  Backend -->|"SQLAlchemy"| DB
```

### 学習計画の流れ

```mermaid
flowchart TD
  A["ユーザーが科目を登録"] --> B["必要時間・完了時間・締切日を保存"]
  B --> C["日本時間の今日を基準にする"]
  C --> D["残り時間を計算"]
  D --> E["締切日までの各日を平日・土日に分類"]
  E --> F["締切・残り時間・達成率・最近未学習から優先度を算出"]
  F --> G["1日の最大科目数までに絞る"]
  G --> H["各日の学習可能時間を重みにして予定時間を算出"]
  H --> I["Dashboard に表示"]
  I --> J["Check-in で実績を分単位入力"]
  J --> K["完了時間を更新"]
  K --> L["翌日以降の計画を再計算"]
  L --> I
  K --> M["日別の予定・実績・達成率を集計"]
  M --> N["締切までの最終達成確率を予測"]
  N --> I
```

### データモデル

```mermaid
erDiagram
  USERS ||--o| STUDY_SETTINGS : has
  USERS ||--o{ SUBJECTS : owns
  SUBJECTS ||--o{ STUDY_PLANS : has
  SUBJECTS ||--o{ STUDY_LOGS : records

  USERS {
    int id
    string email
    string hashed_password
    datetime created_at
  }

  STUDY_SETTINGS {
    int id
    int user_id
    float daily_available_hours
    float weekday_available_hours
    float weekend_available_hours
    string morning_webhook_url
    int max_daily_subjects
  }

  SUBJECTS {
    int id
    int user_id
    string name
    date deadline_date
    float required_hours
    float completed_hours
    string status
  }

  STUDY_PLANS {
    int id
    int user_id
    int subject_id
    date plan_date
    float planned_hours
    float priority_score
    string priority_reasons
    string status
  }

  STUDY_LOGS {
    int id
    int user_id
    int subject_id
    date log_date
    float planned_hours
    float actual_hours
    bool did_study
    string note
  }
```

### 設定カラム

`study_settings` には、時間管理の基準として次のカラムを持たせています。

| カラム | 役割 |
| --- | --- |
| `daily_available_hours` | 既存データとの互換用の 1 日学習可能時間 |
| `weekday_available_hours` | 平日に確保できる学習時間 |
| `weekend_available_hours` | 土日に確保できる学習時間 |
| `morning_webhook_url` | 毎朝の学習ブリーフィング送信用 Webhook URL |
| `max_daily_subjects` | Dashboard に表示する 1 日あたりの最大科目数 |

既存データベース向けには `backend/alembic/versions/0002_weekend_study_settings.py` でカラムを追加し、既存の `daily_available_hours` から初期値を引き継ぎます。`CREATE_TABLES_ON_STARTUP=true` の環境では、起動時にも不足カラムを補完します。
Webhook URL は `backend/alembic/versions/0003_morning_webhook_settings.py` で追加します。
1 日あたりの最大科目数と優先度の保存カラムは `backend/alembic/versions/0004_daily_subject_limit_priority.py` で追加します。

### 画面設計

| 画面 | 役割 |
| --- | --- |
| Signup / Login | ユーザー登録・ログイン |
| Dashboard | 今日の予定、科目数制限、優先度理由、最終達成確率、日別達成率、残り割合、ポモドーロタイマーを表示 |
| Subjects | 科目一覧、必要時間編集、残り割合確認、科目削除 |
| Add Subject | 新しい科目の登録 |
| Settings | 平日・土日の学習可能時間、1 日の最大科目数、Webhook URL を設定 |
| Check-in | 今日の実績を分単位で入力 |

## 学習計画の計算式

現在の計画生成は LLM ではなく、シンプルな数式ベースです。日付は `Asia/Tokyo` の現在日付を基準にします。

```text
remaining_hours = required_hours - completed_hours
priority_score = 締切の近さ + 学習圧 + 達成率の低さ + 最近未学習度
selected_subjects = priority_score 上位 max_daily_subjects 件
available_hours_for_day = 平日なら weekday_available_hours、土日なら weekend_available_hours
future_available_hours = 今日から締切日までの available_hours_for_day の合計
planned_hours_for_day = remaining_hours * (available_hours_for_day / future_available_hours)
```

実績を入力すると `completed_hours` が更新され、残り時間・現在日付・平日/土日の学習可能時間から計画が再計算されます。

## 科目制限と優先度スコア

科目が多すぎると 1 日の学習が細切れになるため、Settings で `一日の最大科目数` を設定できます。初期値は 3 科目です。

計画生成時は各科目を特徴量ベースでスコアリングし、1 日ごとに上位 N 科目だけを Dashboard に表示します。

```text
priority_score =
  締切の近さ
+ 1日あたり必要な学習圧
+ 達成率の低さ
+ 最近未学習である度合い
```

これは外部の ML API を使うものではなく、機械学習の特徴量設計を模した説明可能なスコアリングです。選ばれなかった科目は消えるのではなく、翌日以降に残り時間が再配分されます。

Dashboard では、選ばれた理由として次のようなラベルを表示します。

- 締切が近い
- 必要時間が重い
- 達成率が低い
- 最近未学習

## 最終達成確率の予測

Check-in で入力された科目別実績は、日付ごとに合算されます。

```text
daily_planned_hours = その日の予定時間の合計
daily_actual_hours = その日の実績時間の合計
achievement_rate = daily_actual_hours / daily_planned_hours * 100
recent_execution_rate = 直近の実績時間合計 / 直近の予定時間合計
projected_capacity = 締切までの学習可能時間 * recent_execution_rate
subject_probability = 締切順に共有キャパシティを割り当て、残り必要時間との比率から推定
final_completion_probability = 科目別 probability の最小値
```

Dashboard では、今日のノルマ達成率ではなく「締切までに必要学習時間を完了できる確率」を表示します。複数科目で同じ学習時間を二重計上しないように、締切が早い科目から共有された学習可能時間を割り当て、科目別の最終達成確率と全体の最終達成確率を推定します。LLM API は使わず、保存済みの学習ログから数式ベースで分析します。

最終達成確率の判定は、33% 以下を `要再計画`、34〜67% を `調整圏`、68% 以上を `継続圏` とします。低確率時は学習時間、科目数制限、必要時間、締切の見直しを促し、中間帯では日々の実行率改善を促す設計です。

## 毎朝 Webhook 通知

Settings で Webhook URL を保存すると、バックエンドの Vercel Cron が毎朝学習ブリーフィングを送信します。

通知内容:

- 今日の予定学習時間
- 学習可能時間
- 最終達成確率
- 残り必要時間
- 予測可能学習時間
- 今日やる科目と予定時間

Vercel Cron の時刻は UTC 基準です。`backend/vercel.json` では `0 22 * * *` を設定しており、日本時間の毎朝 7 時台に `/cron/morning-summary` を実行します。

## ポモドーロタイマー

Dashboard には 15 分学習 / 5 分休憩のポモドーロタイマーがあります。

1 日の学習可能時間から、15 分タイマーを何回回せばよいかを表示します。

例:

```text
1日の勉強時間 2時間
8回
15分タイマーを8回回すと達成できます。
```

## 技術構成

| 領域 | 技術 |
| --- | --- |
| Frontend | Next.js App Router, React, TypeScript |
| UI | CSS, lucide-react |
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Migration | Alembic |
| Database | PostgreSQL |
| Auth | JWT |
| Frontend Deploy | Vercel |
| Backend Deploy | Vercel |
| Database Hosting | Neon / Supabase など |

## ディレクトリ構成

```text
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── server.py
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── vercel.json
├── docker-compose.yml
├── requirements.txt
├── server.py
└── README.md
```

## ローカル起動

### 1. PostgreSQL を起動

```bash
docker compose up -d db
```

### 2. Backend を起動

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Backend は `http://localhost:8000` で起動します。

### 3. Frontend を起動

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend は `http://localhost:3000` で起動します。

## 環境変数

### Backend

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/schedulesystemai
SECRET_KEY=change-this-secret-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080
BACKEND_CORS_ORIGINS=http://localhost:3000
CREATE_TABLES_ON_STARTUP=true
APP_TIMEZONE=Asia/Tokyo
CRON_SECRET=change-this-cron-secret
```

### Frontend

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## デプロイ

このアプリケーションは frontend と backend を別々の Vercel Project としてデプロイします。

### Frontend

- Root Directory: `frontend`
- Framework Preset: `Next.js`
- Build Command: `npm run build`
- Install Command: `npm install`
- Environment Variables:
  - `NEXT_PUBLIC_API_BASE_URL=https://your-backend.vercel.app`

本番 Frontend URL:

```text
https://schedule-system-ai.vercel.app/
```

### Backend

- Root Directory: `backend`
- Framework Preset: `Other` または `Python`
- Build Command: 空でよい
- Environment Variables:
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app`
  - `CREATE_TABLES_ON_STARTUP=true`
  - `APP_TIMEZONE=Asia/Tokyo`
  - `CRON_SECRET`

Backend の Vercel Project では `backend/vercel.json` により、毎朝通知用の Cron Job が登録されます。Vercel の `CRON_SECRET` は Cron 実行時に `Authorization: Bearer <CRON_SECRET>` として送られ、バックエンド側で検証します。

Backend のデプロイ後、次の URL が応答すれば成功です。

```text
https://your-backend.vercel.app/health
```

期待されるレスポンス:

```json
{
  "status": "ok",
  "database": {
    "status": "ok"
  }
}
```

## 今後の拡張案

- Gemini Flash などの LLM を使った学習計画の提案
- 週単位・月単位の進捗レポート
- ポモドーロ完了回数の保存
- 試験別テンプレートの追加

## License

MIT License
