import type { Metadata } from "next";

import { AppHeader } from "@/components/AppHeader";

import "./globals.css";

export const metadata: Metadata = {
  title: "VLearn Slide Quiz",
  description: "Chọn bộ slide ngày 1 hoặc ngày 2 và tạo quiz tổng hợp.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body>
        <AppHeader />
        <main className="page-shell">{children}</main>
      </body>
    </html>
  );
}
