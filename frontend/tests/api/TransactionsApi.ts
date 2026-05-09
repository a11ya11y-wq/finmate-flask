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

        expect(response.ok()).toBeTruthy();
        return await response.json();
    }
}