import { expect } from "@playwright/test";
import { BaseApi } from "./BaseApi";
import { CategoryResponse } from "../interfaces/categories";

export class CategoriesApi extends BaseApi {
    
    async getCategoryIdByName(name: string) {

        const response = await this.request.get(`${this.baseUrl}/categories/all`, {
            headers: {
                'Authorization': `Bearer ${this.apiToken}`,
                'Content-Type': 'application/json'
            }
        });
        expect(response.ok()).toBeTruthy();
        
        const body = await response.json();
        const categories = body.data;

        const category = categories.find((cat: CategoryResponse) => cat.name === name);

        if (!category) {
            throw new Error(`Category with name '${name}' not found`);
        }

        return category.id;
    }
}