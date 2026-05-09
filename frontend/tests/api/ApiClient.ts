import { APIRequestContext } from "@playwright/test";
import { AuthApi } from "./AuthApi";
import { CategoriesApi } from "./CategoriesApi";
import { TransactionsApi } from "./TransactionsApi";


export class ApiClient {
    readonly request: APIRequestContext;

    // Our modules
    readonly auth: AuthApi;
    readonly categories: CategoriesApi;
    readonly transactions: TransactionsApi;

    constructor(request: APIRequestContext) {
        this.request = request;
        this.auth = new AuthApi(request);
        this.categories = new CategoriesApi(request);
        this.transactions = new TransactionsApi(request);
    }

    setToken(token: string) {
        this.auth.apiToken = token;
        this.categories.apiToken = token;
        this.transactions.apiToken = token;
    }
}