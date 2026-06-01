"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpen, CalendarDays, CheckCircle2, Clock, LogOut, Plus } from "lucide-react";
import { clearToken } from "@/lib/api";

export function NavShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/");
  }

  return (
    <main className="page">
      <div className="topbar">
        <Link href="/dashboard" className="brand">
          ScheduleSystemAI
        </Link>
        <nav className="nav" aria-label="Main navigation">
          <Link href="/dashboard">
            <CalendarDays size={17} />
            Dashboard
          </Link>
          <Link href="/subjects">
            <BookOpen size={17} />
            Subjects
          </Link>
          <Link href="/subjects/new">
            <Plus size={17} />
            Add
          </Link>
          <Link href="/settings">
            <Clock size={17} />
            Time
          </Link>
          <Link href="/checkin">
            <CheckCircle2 size={17} />
            Check-in
          </Link>
          <button className="ghost-button" type="button" onClick={logout} aria-label="Logout">
            <LogOut size={17} />
          </button>
        </nav>
      </div>
      {children}
    </main>
  );
}
