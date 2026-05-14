import { Page, Locator } from "@playwright/test";
import { BaseCategoryModal } from "./BaseCategoryModal";

export class CreateCategoryModal extends BaseCategoryModal {
    readonly addCategoryButton: Locator;

    constructor(page: Page) {
        super(page);
         this.addCategoryButton = this.page.getByRole('button', { name: 'Add Category' });
    }
}