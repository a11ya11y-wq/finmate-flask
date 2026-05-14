import { Page, Locator } from '@playwright/test';
import { BasePage } from '../common/BasePage';
import { EditProfileModal } from './components/EditProfileModal';
import { ProfileUserInfo } from './components/ProfileUserInfo';
import { ProfileChangePasswordModal } from './components/ProfileChangePasswordModal';
import { MonobankIntegrationModal } from './components/MonobankIntegrationModal';
import { ConfirmDeleteModal } from '../common/components/ConfirmDeleteModal';
import { ProfileCategoriesSection } from './components/ProfileCategoriesSection';
import { CreateCategoryModal } from './components/CreateCategoryModal';
import { EditCategoryModal } from './components/EditCategoryModal';

export class ProfilePage extends BasePage {
    readonly page: Page;

    readonly userInfo: ProfileUserInfo;

    readonly editProfileButton: Locator;
    readonly editProfileModal: EditProfileModal;

    readonly changePasswordButton: Locator;
    readonly changePasswordModal: ProfileChangePasswordModal;

    readonly monobankIntegrationButton: Locator;
    readonly monobankIntegrationModal: MonobankIntegrationModal;

    readonly categoriesSection: ProfileCategoriesSection;
    readonly createCategoryModal: CreateCategoryModal;
    readonly editCategoryModal: EditCategoryModal;

    readonly deleteAccountButton: Locator;
    readonly confirmDeleteModal: ConfirmDeleteModal;

    constructor(page: Page) {
        super(page);
        this.page = page;

        this.userInfo = new ProfileUserInfo(page);

        this.editProfileButton = page.getByTestId('quick-action-edit-profile');
        this.editProfileModal = new EditProfileModal(page);

        this.changePasswordButton = page.getByTestId('quick-action-security');
        this.changePasswordModal = new ProfileChangePasswordModal(page);

        this.monobankIntegrationButton = page.getByTestId('quick-action-monobank');
        this.monobankIntegrationModal = new MonobankIntegrationModal(page);
        this.confirmDeleteModal = new ConfirmDeleteModal(page);

        this.categoriesSection = new ProfileCategoriesSection(page);
        this.createCategoryModal = new CreateCategoryModal(page);
        this.editCategoryModal = new EditCategoryModal(page);

        this.deleteAccountButton = page.getByRole('button', { name: 'Delete Account' });
    }

    async goto() {
        await this.page.goto('/profile');
    }
}