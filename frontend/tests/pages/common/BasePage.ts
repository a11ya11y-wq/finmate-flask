import { Page } from '@playwright/test'
import { Header } from './components/Header';
import { Toast } from './components/Toast';


export class BasePage {
    readonly page: Page
    readonly header: Header
    readonly toast: Toast

    constructor(page: Page) {
        this.page = page;
        this.header = new Header(page);
        this.toast = new Toast(page);
    }
}