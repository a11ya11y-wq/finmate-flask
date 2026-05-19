import { Locator, Page } from '@playwright/test';
import { BasePage } from '../common/BasePage';
import { BudgetForm } from './components/BudgetForm';
import { BudgetCard } from './components/BudgetCard';
import { ConfirmDeleteModal } from '../common/components/ConfirmDeleteModal';

export class BudgetsPage extends BasePage {
    protected readonly url = '/budgets';

    readonly budgetLimitContainer: Locator

    readonly budgetForm: BudgetForm;

    readonly budgetCards: BudgetCard;

    readonly confirmDeleteModal: ConfirmDeleteModal;

    constructor(page: Page) {
        super(page);
        
        this.budgetLimitContainer = page.getByTestId('budgets-limit-container');

        this.budgetForm = new BudgetForm(page);
        this.budgetCards = new BudgetCard(page);

        this.confirmDeleteModal = new ConfirmDeleteModal(page);
    }
}