import { expect } from '@playwright/test';
import { BaseApi } from './BaseApi';
import { RegisterRequest } from '../interfaces/auth';


export interface AuthCookie {
    name: string;
    value: string;
    url?: string;
    domain?: string;
    path?: string;
    expires?: number;
    httpOnly?: boolean;
    secure?: boolean;
    sameSite?: 'Strict' | 'Lax' | 'None';
}

export class AuthApi extends BaseApi {

    async register(payload: RegisterRequest) {
        const response = await this.request.post(`${this.baseUrl}/auth/register`, {
            data: {
                username: payload.username,
                password: payload.password,
                confirm_password: payload.confirmPassword,
                email: payload.email
            }
        });
        expect(response.ok(), `Registration failed: ${await response.text()}`).toBeTruthy();
    }

    async loginAndGetCookies(email: string, password: string): Promise<AuthCookie[]> {
        const response = await this.request.post(`${this.baseUrl}/auth/login`, {
            data: {
                email,
                password
            }
        });
        expect(response.ok(), `Login failed: ${await response.text()}`).toBeTruthy();
        const body = await response.json();
        this.apiToken = body.access_token; // Store the token for future requests

        const headers = response.headers(); // Get all headers from the response
        const setCookieHeader = headers['set-cookie']; // Extract the 'set-cookie' header

        if (!setCookieHeader) {
            throw new Error('No Set-Cookie header found in the response');
        }

        const match = setCookieHeader.match(/finmate_refresh_token=([^;]+)/);
        if (!match) {
            throw new Error('Incorect Set-Cookie header format, finmate_refresh_token not found');
        }

        return [{
            name: 'finmate_refresh_token',
            value: match[1],
            domain: 'localhost',
            path: '/',
            httpOnly: true,
            secure: false,
            sameSite: 'Lax'
        }]
    }
}