import { Page } from "@playwright/test";
import { AddTransactionFormData } from "../../../interfaces/transaction";
import { BaseTransactionModal } from "./BaseTransactionModal";


export class AddTransactionModal extends BaseTransactionModal {
    constructor(page: Page) {
        super(page, /Add Transaction/i);
    }

    async fillForm(data: AddTransactionFormData) {
        await super.fillForm(data);
    }
}