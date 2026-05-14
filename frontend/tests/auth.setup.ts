import { test as setup } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config();
const authFile = 'tests/.auth/user.json';

setup('authenticate API only', async ({ request }) => {
    const email = process.env.USER_EMAIL;
    const password = process.env.USER_PASSWORD;
    const apiUrl = process.env.VITE_API_URL || 'http://localhost:5000';

    await request.post(`${apiUrl}/api/v1/auth/register`, {
        data: { email, password, username: 'test_setup', confirm_password: password }
    });

    const loginResponse = await request.post(`${apiUrl}/api/v1/auth/login`, {
        data: { email, password }
    });

    if (!loginResponse.ok()) {
        throw new Error(`API Login failed: ${await loginResponse.text()}`);
    }

    await request.storageState({ path: authFile });
});