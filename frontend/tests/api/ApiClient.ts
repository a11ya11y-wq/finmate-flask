import { APIRequestContext } from "@playwright/test";
import { AuthApi } from "./AuthApi";
import { CategoriesApi } from "./CategoriesApi";
import { TransactionsApi } from "./TransactionsApi";
import { BudgetsApi } from "./BudgetsApi";

export class ApiClient {
    readonly request: APIRequestContext;

    // Our modules
    readonly auth: AuthApi;
    readonly categories: CategoriesApi;
    readonly transactions: TransactionsApi;
    readonly budgets: BudgetsApi;

    constructor(request: APIRequestContext) {
        this.request = request;
        this.auth = new AuthApi(request);
        this.categories = new CategoriesApi(request);
        this.transactions = new TransactionsApi(request);
        this.budgets = new BudgetsApi(request);
    }

    setToken(token: string) {
        this.auth.apiToken = token;
        this.categories.apiToken = token;
        this.transactions.apiToken = token;
        this.budgets.apiToken = token;
    }
}