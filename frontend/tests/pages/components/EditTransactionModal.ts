import { Page } from "@playwright/test";
import { BaseTransactionModal } from "./BaseTransactionModal";


export class EditTransactionModal extends BaseTransactionModal {
    constructor(page: Page) {
        super(page, /Save Changes/i);
    }
}