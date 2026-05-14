import { test, expect } from '../fixtures/dynamicUserFixture';
import { ProfilePage } from '../pages/profile/ProfilePage';



test.describe('Profile Page', () => {
    test('User can edit their profile', async ({ page }) => {
        const profilePage = new ProfilePage(page);

        await profilePage.goto();

        const originalAvatarSrc = await profilePage.userInfo.avatar.getAttribute('src');

        await profilePage.editProfileButton.click();
        await expect(profilePage.editProfileModal.container).toBeVisible();

        const newUsername = `NewUsername${Date.now()}`;
        await profilePage.editProfileModal.usernameInput.fill(newUsername);
        await profilePage.editProfileModal.currencySelect.selectOption('EUR');
        await profilePage.editProfileModal.selectAvatarByIndex(3);

        await profilePage.editProfileModal.saveButton.click();
        await profilePage.toast.expectSuccess('Profile updated');

        await expect(profilePage.editProfileModal.container).not.toBeVisible();

        await expect(profilePage.userInfo.username).toHaveText(newUsername);
        await expect(profilePage.userInfo.currency).toHaveText('EUR'); // Stock currency is USD
        const newAvatarSrc = await profilePage.userInfo.avatar.getAttribute('src');
        expect(newAvatarSrc).not.toBe(originalAvatarSrc);
    });
    test.describe('Change Password', () => {
        test('User can change password', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();
            await profilePage.changePasswordButton.click();
            await expect(profilePage.changePasswordModal.container).toBeVisible();

            await profilePage.changePasswordModal.currentPasswordInput.fill('TestPassword123');
            await profilePage.changePasswordModal.newPasswordInput.fill('newpassword123');
            await profilePage.changePasswordModal.confirmNewPasswordInput.fill('newpassword123');

            await profilePage.changePasswordModal.saveButton.click();
            await profilePage.toast.expectSuccess('Password updated successfully');

            await expect(profilePage.changePasswordModal.container).not.toBeVisible();
        });

        test('User sees validation errors when changing password with empty fields', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();
            await profilePage.changePasswordButton.click();
            await expect(profilePage.changePasswordModal.container).toBeVisible();

            await profilePage.changePasswordModal.saveButton.click();
            await profilePage.toast.expectError('String should have at least 1 character');
        });

        test('User sees validation error when new password and confirm password do not match', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();
            await profilePage.changePasswordButton.click();
            await expect(profilePage.changePasswordModal.container).toBeVisible();

            await profilePage.changePasswordModal.currentPasswordInput.fill('TestPassword123');
            await profilePage.changePasswordModal.newPasswordInput.fill('newpassword123');
            await profilePage.changePasswordModal.confirmNewPasswordInput.fill('differentpassword123');

            await profilePage.changePasswordModal.saveButton.click();
            await profilePage.toast.expectError('Value error, New password and confirmation do not match');
        });

        test('User sees error when current password match with new password', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();
            await profilePage.changePasswordButton.click();
            await expect(profilePage.changePasswordModal.container).toBeVisible();
            await profilePage.changePasswordModal.currentPasswordInput.fill('TestPassword123');
            await profilePage.changePasswordModal.newPasswordInput.fill('TestPassword123');
            await profilePage.changePasswordModal.confirmNewPasswordInput.fill('TestPassword123');
            
            await profilePage.changePasswordModal.saveButton.click();
            await profilePage.toast.expectError('Value error, New password cannot be the same as old password');
        });

        test('User sees error when current password is incorrect', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();
            await profilePage.changePasswordButton.click();
            await expect(profilePage.changePasswordModal.container).toBeVisible();
            await profilePage.changePasswordModal.currentPasswordInput.fill('WrongCurrentPassword');
            await profilePage.changePasswordModal.newPasswordInput.fill('newpassword123');
            await profilePage.changePasswordModal.confirmNewPasswordInput.fill('newpassword123');
            
            await profilePage.changePasswordModal.saveButton.click();
            await profilePage.toast.expectError('Invalid old password.');
        });

    });
    test.describe('Monobank Integration', () => {
        test('User can connect to Monobank', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();

            await profilePage.monobankIntegrationButton.click();

            await profilePage.monobankIntegrationModal.apiKeyInput.fill('valid-monobank-api-token');
            await profilePage.monobankIntegrationModal.saveButton.click();

            await profilePage.toast.expectSuccess('Monobank token saved');

            await profilePage.monobankIntegrationButton.click(); 
            await expect(profilePage.monobankIntegrationModal.disconnectMonotoken).toBeVisible();
        });

        test('User can disconnect from Monobank', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();

            await profilePage.monobankIntegrationButton.click();

            await profilePage.monobankIntegrationModal.apiKeyInput.fill('valid-monobank-api-token');
            await profilePage.monobankIntegrationModal.saveButton.click();

            await profilePage.monobankIntegrationButton.click(); 
            await profilePage.monobankIntegrationModal.disconnectMonotoken.click();
            await profilePage.confirmDeleteModal.deleteButton.click();

            await profilePage.toast.expectSuccess('Monobank token removed');
        });

        test('User sees error when entering invalid Monobank API token', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();

            await profilePage.monobankIntegrationButton.click();

            await profilePage.monobankIntegrationModal.apiKeyInput.fill('123');
            await profilePage.monobankIntegrationModal.saveButton.click();

            await profilePage.toast.expectError('String should have at least 10 characters');
        })
    });
    test('User can delete their account', async ({ page }) => {
        const profilePage = new ProfilePage(page);
        await profilePage.goto();

        await profilePage.deleteAccountButton.click();
        await profilePage.confirmDeleteModal.deleteButton.click();
        await expect(profilePage.page).toHaveURL('/login');
    });

    test.describe('Categories', () => {
        test('User can create a new category', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();

            await profilePage.categoriesSection.addNewButton.click();
            await profilePage.createCategoryModal.nameInput.fill('Test Category');
            await profilePage.createCategoryModal.mccCodeInput.fill('1234');
            await profilePage.createCategoryModal.selectIconByIndex(2);
            await profilePage.createCategoryModal.addCategoryButton.click();

            await profilePage.toast.expectSuccess('Category added!');

            const categoryCard = await profilePage.categoriesSection.getCategoryCardByName('Test Category');
            await expect(categoryCard).toBeVisible();
            await expect(categoryCard).toContainText('1234');

        });

        test('User sees validation errors when creating category with empty fields', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();

            await profilePage.categoriesSection.addNewButton.click();
            await profilePage.createCategoryModal.addCategoryButton.click();

            await profilePage.toast.expectError('String should have at least 1 character');
        });

        test('User can delete a category', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();

            // Delete a stock category (e.g. "Food")
            const categoryCard = await profilePage.categoriesSection.getCategoryCardByName('Food');
            await profilePage.categoriesSection.OpenDeleteModalFor('Food');

            await profilePage.confirmDeleteModal.deleteButton.click();
            await profilePage.toast.expectSuccess('Category deleted');

            await expect(categoryCard).not.toBeVisible();
        });

        test('User can edit a category', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            await profilePage.goto();

            // Edit a stock category (e.g. "Transport")
            const categoryCard = await profilePage.categoriesSection.getCategoryCardByName('Transport');
            await profilePage.categoriesSection.OpenEditModalFor('Transport');

            await profilePage.editCategoryModal.nameInput.fill('Updated Transport');
            await profilePage.editCategoryModal.mccCodeInput.fill('5678');
            await profilePage.editCategoryModal.selectIconByIndex(4);
            await profilePage.editCategoryModal.saveChangesButton.click();

            await profilePage.toast.expectSuccess('Category updated successfully!');

            await expect(categoryCard).toBeVisible();
            await expect(categoryCard).toContainText('Updated Transport');
            await expect(categoryCard).toContainText('5678');
        });
    });
}); 