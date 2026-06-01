import { expect, test } from "@playwright/test";
import dotenv from "dotenv";
import { LoginPage } from "../pages/auth/LoginPage";
import { DashboardPage } from "../pages/dashboard/DashboardPage";

dotenv.config();

const email = process.env.USER_EMAIL || "testemail@gmail.com";
const password = process.env.USER_PASSWORD || "Test123123";

test.use({ storageState: { cookies: [], origins: [] } });

test("restores the session after a hard reload", async ({ page }) => {
  const loginPage = new LoginPage(page);
  const dashboardPage = new DashboardPage(page);

  await loginPage.goto();
  await loginPage.login(email, password);

  await expect(page).toHaveURL(/.*\/dashboard/);

  await page.reload();

  await expect(page).toHaveURL(/.*\/dashboard/);
  await expect(dashboardPage.toolbar.title).toBeVisible();
});