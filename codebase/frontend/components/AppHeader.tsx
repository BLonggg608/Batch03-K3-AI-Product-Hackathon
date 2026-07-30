"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const steps = [
  { label: "Chọn ngày", match: (path: string) => path === "/" },
  { label: "Quiz", match: (path: string) => path.startsWith("/quiz") },
  { label: "Kết quả", match: (path: string) => path.startsWith("/result") },
  { label: "Ôn tập", match: (path: string) => path.startsWith("/review") },
];

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="site-header">
      <div className="header-inner">
        <Link href="/" className="brand" aria-label="VLearn Focus">
          <span className="brand-mark">VF</span>
          <span>
            <strong>VLearn Focus</strong>
            <small>Quiz tổng hợp theo từng ngày học</small>
          </span>
        </Link>
        <nav className="workflow" aria-label="Tiến trình học">
          {steps.map((step, index) => (
            <span
              className={step.match(pathname) ? "workflow-step active" : "workflow-step"}
              key={step.label}
            >
              <b>{index + 1}</b>
              {step.label}
            </span>
          ))}
        </nav>
      </div>
    </header>
  );
}
