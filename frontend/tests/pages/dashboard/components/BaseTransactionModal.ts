import { Page, Locator } from "@playwright/test";
import { AddTransactionFormData } from "../../../interfaces/transaction";


export class BaseTransactionModal {
    readonly page: Page;
    readonly modalFieldsContainer: Locator;

    readonly titleInput: Locator;
    // Type btns
    readonly expenseTypeBtn: Locator;
    readonly incomeTypeBtn: Locator;

    readonly amountInput: Locator;
    readonly categorySelect: Locator;
    readonly dateInput: Locator;
    readonly noteInput: Locator;

    // Buttons
    readonly submitButton: Locator;
    readonly cancelButton: Locator;

    constructor(page: Page, submitButtonText: RegExp) {
        this.page = page;
        this.modalFieldsContainer = page.getByTestId('transaction-form-fields');

        this.titleInput = this.modalFieldsContainer.getByLabel('Title');
        
        this.expenseTypeBtn = this.modalFieldsContainer.getByRole('button', { name: 'Expense' });
        this.incomeTypeBtn = this.modalFieldsContainer.getByRole('button', { name: 'Income' });
        
        this.amountInput = this.modalFieldsContainer.getByLabel('Amount');
        this.categorySelect = this.modalFieldsContainer.getByLabel('Category');
        this.dateInput = this.modalFieldsContainer.getByLabel('Date');
        this.noteInput = this.modalFieldsContainer.getByLabel('Note');

        this.submitButton = this.page.getByRole('button', { name: submitButtonText }); // Add/Save Changes
        this.cancelButton = this.page.getByRole('button', { name: /Cancel/i });
    }

    async fillForm(data: Partial<AddTransactionFormData>) {
        if (data.title) await this.titleInput.fill(data.title);

        if (data.type) {
            if (data.type === 'Expense') await this.expenseTypeBtn.click();
            else await this.incomeTypeBtn.click();
        }
        if (data.amount) await this.amountInput.fill(data.amount.toString());
        if (data.category) await this.categorySelect.selectOption(data.category);
        if (data.date) await this.dateInput.fill(data.date);
        if (data.note !== undefined) await this.noteInput.fill(data.note);
    }
    async submit() {
        await this.submitButton.click();
    }

    async cancel() {
        await this.cancelButton.click();
    }
}