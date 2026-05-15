import { Page, Locator } from "@playwright/test";
import { BaseCategoryModal } from "./BaseCategoryModal";



export class EditCategoryModal extends BaseCategoryModal {
    readonly saveChangesButton: Locator;

    constructor(page: Page) {
        super(page);
        this.saveChangesButton = this.page.getByRole('button', { name: 'Save Changes' });
    }
}