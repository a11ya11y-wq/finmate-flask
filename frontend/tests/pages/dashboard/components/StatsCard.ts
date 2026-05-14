import { Locator, Page } from '@playwright/test';


export class StatsCard {
    readonly container: Locator;
    readonly title: Locator;
    readonly amount: Locator;
    readonly badge: Locator; // Status or change indicator

    constructor(page: Page, testIdPrefix: string) {
        this.container = page.getByTestId(testIdPrefix);
        this.title = this.container.getByTestId(`${testIdPrefix}-title`);
        this.amount = this.container.getByTestId(`${testIdPrefix}-amount`);
        this.badge = this.container.locator('[data-testid$="-change"], [data-testid$="-status"]');
    }

}