import { expect } from "@playwright/test";
import { CreateTransactionRequest } from "../interfaces/transaction";
import { BaseApi } from "./BaseApi";

export class TransactionsApi extends BaseApi {
    

    async createTransaction(payload: CreateTransactionRequest) {

        const response = await this.request.post(`${this.baseUrl}/transactions`, {
            headers: {
                'Authorization': `Bearer ${this.apiToken}`,
                'Content-Type': 'application/json'
            },
            data: payload
        });

        console.log('🔥 Response status from API (Create tx):', response.status());
        console.log('📦 Response from API (Create tx):', await response.text());

        expect(response.ok()).toBeTruthy();
        return await response.json();
    }
}