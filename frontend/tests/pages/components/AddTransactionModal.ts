import { Page, Locator } from "@playwright/test";
import { AddTransactionFormData } from "../../interfaces/transaction";


export class AddTransactionModal {
    readonly page: Page;
    readonly container: Locator;

    titleInput: Locator;
    // Type btns
    expenseTypeBtn: Locator;
    incomeTypeBtn: Locator;

    amountInput: Locator;
    categorySelect: Locator;
    dateInput: Locator;
    noteInput: Locator;

    // Buttons
    submitButton: Locator;
    cancelButton: Locator;

    constructor(page: Page) {
        this.page = page;
        this.container = page.getByTestId('transaction-form-fields');
        this.titleInput = this.container.getByLabel('Title');
        this.expenseTypeBtn = this.container.getByRole('button', { name: 'Expense' });
        this.incomeTypeBtn = this.container.getByRole('button', { name: 'Income' });
        this.amountInput = this.container.getByLabel('Amount');
        this.categorySelect = this.container.getByLabel('Category');
        this.dateInput = this.container.getByLabel('Date');
        this.noteInput = this.container.getByLabel('Note');
        this.submitButton = this.page.getByRole('button', { name: /Add Transaction/i });
        this.cancelButton = this.page.getByRole('button', { name: /Cancel/i });
    }

    async fillForm(data: AddTransactionFormData) {
        await this.titleInput.fill(data.title);
        if (data.type === 'Expense') {
            await this.expenseTypeBtn.click();
        } else {
            await this.incomeTypeBtn.click();
        }
        await this.amountInput.fill(data.amount.toString());
        await this.categorySelect.selectOption(data.category);
        if (data.date) {
            await this.dateInput.fill(data.date);
        }
        if (data.note) {
            await this.noteInput.fill(data.note);
        };
    }

    async submit() {
        await this.submitButton.click();
    }

    async cancel() {
        await this.cancelButton.click();
    }
}