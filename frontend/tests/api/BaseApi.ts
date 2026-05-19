import { APIRequestContext } from "@playwright/test";
import dotenv from 'dotenv';


dotenv.config();


export class BaseApi {
    readonly request: APIRequestContext;
    public apiToken: string | null = null;

    protected baseUrl = process.env.API_URL || 'http://localhost:5000/api/v1';

    constructor(request: APIRequestContext) {
        this.request = request;
    }

    
}