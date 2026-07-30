import { existsSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

import { chromium } from "playwright-core";

const executablePath = [
  process.env.BROWSER_EXECUTABLE,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
]
  .filter(Boolean)
  .find((candidate) => existsSync(candidate));
if (!executablePath) throw new Error("Không tìm thấy Chrome hoặc Edge.");

const artifacts = resolve("artifacts");
const appUrl = process.env.SMOKE_APP_URL || "http://127.0.0.1:3000";
mkdirSync(artifacts, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});
page.on("response", (response) => {
  if (response.status() >= 400) errors.push(`HTTP ${response.status()}: ${response.url()}`);
});

try {
  await page.goto(appUrl, { waitUntil: "networkidle" });
  await page.getByText("Chọn bộ slide muốn tạo quiz").waitFor();
  if ((await page.locator(".deck-card").count()) !== 2) {
    throw new Error("Trang chủ phải có đúng hai lựa chọn.");
  }
  await page.screenshot({ path: resolve(artifacts, "01-home.png"), fullPage: true });

  const dayTwoCard = page.locator(".deck-card").nth(1);
  await dayTwoCard.getByRole("button", { name: "Tạo quiz", exact: true }).click();
  await dayTwoCard.getByRole("button", { name: "10 câu", exact: true }).click();
  await page.waitForURL(/\/quiz\//, { timeout: 60000 });
  await page.locator(".question-card").first().waitFor();
  if ((await page.locator(".question-card").count()) !== 10) {
    throw new Error("Quiz chẩn đoán đã chọn phải có 10 câu.");
  }
  for (const card of await page.locator(".question-card").all()) {
    await card.locator('input[type="radio"]').first().check();
  }
  await page.getByRole("button", { name: "Nộp bài" }).click();
  await page.waitForURL(/\/result\//);
  await page.getByText("Evidence trên slide").first().waitFor();
  await page.screenshot({ path: resolve(artifacts, "02-result.png"), fullPage: true });

  await page.getByRole("button", { name: "Tạo gói ôn tập cá nhân" }).click();
  await page.waitForURL(/\/review\//, { timeout: 60000 });
  await page.getByText("Ôn đúng nội dung nguồn").waitFor();
  await page.screenshot({ path: resolve(artifacts, "03-review.png"), fullPage: true });

  await page.getByRole("button", { name: "Làm quiz củng cố" }).click();
  await page.waitForURL(/\/quiz\//, { timeout: 60000 });
  await page.locator(".question-card").first().waitFor();
  if ((await page.locator(".question-card").count()) !== 4) {
    throw new Error("Quiz củng cố phải có 4 câu.");
  }
  for (const card of await page.locator(".question-card").all()) {
    await card.locator('input[type="radio"]').first().check();
  }
  await page.getByRole("button", { name: "Nộp bài" }).click();
  await page.waitForURL(/\/result\/.*compare=1/);
  await page.getByText("Trước ôn tập").waitFor();
  await page.screenshot({ path: resolve(artifacts, "04-progress.png"), fullPage: true });

  if (errors.length) throw new Error(errors.join("\n"));
  console.log(
    "Browser smoke passed: choose day 2 deck -> choose 10 questions -> review -> reinforcement.",
  );
} finally {
  await browser.close();
}
