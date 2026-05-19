import { expect } from "@playwright/test";
import { CreateBudgetRequest } from "../interfaces/budget";
import { BaseApi } from "./BaseApi";


export class BudgetsApi extends BaseApi {

    async createBudget(payload: CreateBudgetRequest) {
        const response = await this.request.post(`${this.baseUrl}/budgets`, {
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