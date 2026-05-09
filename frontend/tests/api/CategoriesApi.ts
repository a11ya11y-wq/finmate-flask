import { expect } from "@playwright/test";
import { BaseApi } from "./BaseApi";

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

        const category = categories.find((cat: any) => cat.name === name);

        if (!category) {
            throw new Error(`Category with name '${name}' not found`);
        }
        console.log(`🔍 Знайдена категорія: ${category.name} (ID: ${category.id})`);
        return category.id;
    }
}