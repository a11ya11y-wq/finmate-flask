import { Page, Locator } from "@playwright/test";
import { BudgetFormData } from "../../../interfaces/budget";


export class BudgetForm {
    readonly page: Page;
    readonly container: Locator;

    readonly categorySelect: Locator;
    readonly amountInput: Locator;

    readonly isRecurringCheckbox: Locator;
    
    readonly saveButton: Locator;
    readonly updateButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('budgets-form-container');

        this.categorySelect = this.container.getByLabel('Category');
        this.amountInput = this.container.getByLabel('Amount');
        this.isRecurringCheckbox = this.container.getByLabel(/Recurring budget/i);

        this.saveButton = this.container.getByRole('button', { name: /Save Budget/i });
        this.updateButton = this.container.getByRole('button', { name: /Update Budget/i });
    }

    async  fillForm(data: BudgetFormData) {
        await this.categorySelect.selectOption(data.category);
        await this.amountInput.fill(data.amount.toString());
        if (data.isRecurring) {
            await this.isRecurringCheckbox.check();
        } else {
            await this.isRecurringCheckbox.uncheck();
        }
    }
}