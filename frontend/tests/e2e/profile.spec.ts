import { test, expect } from '../fixtures/dynamicUserFixture';
import { Locator } from '@playwright/test';
import { ProfilePage } from '../pages/profile/ProfilePage';
import { step } from 'allure-js-commons';

test.describe('Profile Page', () => {
    test('User can edit their profile', async ({ page }) => {
        const profilePage = new ProfilePage(page);
        const newUsername = `NewUsername${Date.now()}`;
        let originalAvatarSrc: string | null = '';

        await step('Navigate to profile page and get original avatar', async () => {
            await profilePage.goto();
            originalAvatarSrc = await profilePage.userInfo.avatar.getAttribute('src');
        });

        await step('Open edit profile modal and fill new data', async () => {
            await profilePage.editProfileButton.click();
            await expect(profilePage.editProfileModal.container).toBeVisible();

            await profilePage.editProfileModal.usernameInput.fill(newUsername);
            await profilePage.editProfileModal.currencySelect.selectOption('EUR');
            await profilePage.editProfileModal.selectAvatarByIndex(3);
        });

        await step('Save changes and verify success message', async () => {
            await profilePage.editProfileModal.saveButton.click();
            await profilePage.toast.expectSuccess('Profile updated');
            await expect(profilePage.editProfileModal.container).not.toBeVisible();
        });

        await step('Verify updated profile information in the UI', async () => {
            await expect(profilePage.userInfo.username).toHaveText(newUsername);
            await expect(profilePage.userInfo.currency).toHaveText('EUR'); // Stock currency is USD
            const newAvatarSrc = await profilePage.userInfo.avatar.getAttribute('src');
            expect(newAvatarSrc).not.toBe(originalAvatarSrc);
        });
    });

    test.describe('Change Password', () => {
        test('User can change password', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            
            await step('Navigate to profile and open change password modal', async () => {
                await profilePage.goto();
                await profilePage.changePasswordButton.click();
                await expect(profilePage.changePasswordModal.container).toBeVisible();
            });

            await step('Fill in current and new password details', async () => {
                await profilePage.changePasswordModal.currentPasswordInput.fill('TestPassword123');
                await profilePage.changePasswordModal.newPasswordInput.fill('newpassword123');
                await profilePage.changePasswordModal.confirmNewPasswordInput.fill('newpassword123');
            });

            await step('Save changes and verify success message', async () => {
                await profilePage.changePasswordModal.saveButton.click();
                await profilePage.toast.expectSuccess('Password updated successfully');
                await expect(profilePage.changePasswordModal.container).not.toBeVisible();
            });
        });

        test('User sees validation errors when changing password with empty fields', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            
            await step('Navigate to profile and open change password modal', async () => {
                await profilePage.goto();
                await profilePage.changePasswordButton.click();
                await expect(profilePage.changePasswordModal.container).toBeVisible();
            });

            await step('Submit empty form and verify validation errors', async () => {
                await profilePage.changePasswordModal.saveButton.click();
                await profilePage.expectFieldError('old-password', 'Enter your current password');
                await profilePage.expectFieldError('new-password', 'New password cannot be empty');
                await profilePage.expectFieldError('confirm-password', 'Confirm your new password');
            });
        });

        test('User sees validation error when new password and confirm password do not match', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            
            await step('Navigate to profile and open change password modal', async () => {
                await profilePage.goto();
                await profilePage.changePasswordButton.click();
                await expect(profilePage.changePasswordModal.container).toBeVisible();
            });

            await step('Fill mismatched new and confirm passwords', async () => {
                await profilePage.changePasswordModal.currentPasswordInput.fill('TestPassword123');
                await profilePage.changePasswordModal.newPasswordInput.fill('newpassword123');
                await profilePage.changePasswordModal.confirmNewPasswordInput.fill('differentpassword123');
            });

            await step('Submit and verify password mismatch error', async () => {
                await profilePage.changePasswordModal.saveButton.click();
                await profilePage.expectFieldError('confirm-password', 'Passwords do not match');
            });
        });

        test('User sees error when current password match with new password', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            
            await step('Navigate to profile and open change password modal', async () => {
                await profilePage.goto();
                await profilePage.changePasswordButton.click();
                await expect(profilePage.changePasswordModal.container).toBeVisible();
            });

            await step('Fill identical current and new passwords', async () => {
                await profilePage.changePasswordModal.currentPasswordInput.fill('TestPassword123');
                await profilePage.changePasswordModal.newPasswordInput.fill('TestPassword123');
                await profilePage.changePasswordModal.confirmNewPasswordInput.fill('TestPassword123');
            });

            await step('Submit and verify duplicate password error', async () => {
                await profilePage.changePasswordModal.saveButton.click();
                await profilePage.expectFieldError('new-password', 'New password cannot be the same as current password');
            });
        });

        test('User sees error when current password is incorrect', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            
            await step('Navigate to profile and open change password modal', async () => {
                await profilePage.goto();
                await profilePage.changePasswordButton.click();
                await expect(profilePage.changePasswordModal.container).toBeVisible();
            });

            await step('Fill incorrect current password', async () => {
                await profilePage.changePasswordModal.currentPasswordInput.fill('WrongCurrentPassword');
                await profilePage.changePasswordModal.newPasswordInput.fill('newpassword123');
                await profilePage.changePasswordModal.confirmNewPasswordInput.fill('newpassword123');
            });

            await step('Submit and verify invalid old password toast error', async () => {
                await profilePage.changePasswordModal.saveButton.click();
                await profilePage.toast.expectError('Invalid old password.');
            });
        });
    });

    test.describe('Monobank Integration', () => {
        test('User can connect to Monobank', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            const validToken: string = 'T'.repeat(44);
            
            await step('Navigate to profile and open Monobank modal', async () => {
                await profilePage.goto();
                await profilePage.monobankIntegrationButton.click();
            });

            await step('Enter valid API token and save', async () => {
                await profilePage.monobankIntegrationModal.apiKeyInput.fill(validToken);
                await profilePage.monobankIntegrationModal.saveButton.click();
                await profilePage.toast.expectSuccess('Monobank token saved');
            });

            await step('Verify disconnect button becomes visible', async () => {
                await profilePage.monobankIntegrationButton.click(); 
                await expect(profilePage.monobankIntegrationModal.disconnectMonotoken).toBeVisible();
            });
        });

        test('User can disconnect from Monobank', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            const validToken: string = 'T'.repeat(44);
            
            await step('Precondition: Connect to Monobank', async () => {
                await profilePage.goto();
                await profilePage.monobankIntegrationButton.click();
                await profilePage.monobankIntegrationModal.apiKeyInput.fill(validToken);
                await profilePage.monobankIntegrationModal.saveButton.click();
            });

            await step('Open Monobank modal and initiate disconnect', async () => {
                await profilePage.monobankIntegrationButton.click(); 
                await profilePage.monobankIntegrationModal.disconnectMonotoken.click();
            });

            await step('Confirm deletion and verify success message', async () => {
                await profilePage.confirmDeleteModal.deleteButton.click();
                await profilePage.toast.expectSuccess('Monobank token removed');
            });
        });

        test('User sees error when entering invalid Monobank API token', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            
            await step('Navigate to profile and open Monobank modal', async () => {
                await profilePage.goto();
                await profilePage.monobankIntegrationButton.click();
            });

            await step('Enter short invalid token and submit', async () => {
                await profilePage.monobankIntegrationModal.apiKeyInput.fill('123');
                await profilePage.monobankIntegrationModal.saveButton.click();
            });

            await step('Verify token length validation error', async () => {
                await profilePage.expectFieldError('token', 'Token must be exactly 44 characters');
            });
        });
    });

    test('User can delete their account', async ({ page }) => {
        const profilePage = new ProfilePage(page);
        
        await step('Navigate to profile', async () => {
            await profilePage.goto();
        });

        await step('Initiate account deletion and confirm', async () => {
            await profilePage.deleteAccountButton.click();
            await profilePage.confirmDeleteModal.deleteButton.click();
        });

        await step('Verify user is redirected to login page', async () => {
            await expect(profilePage.page).toHaveURL('/login');
        });
    });

    test.describe('Categories', () => {
        test('User can create a new category', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            
            await step('Navigate to profile and open add category modal', async () => {
                await profilePage.goto();
                await profilePage.categoriesSection.addNewButton.click();
            });

            await step('Fill out new category details and submit', async () => {
                await profilePage.createCategoryModal.nameInput.fill('Test Category');
                await profilePage.createCategoryModal.mccCodeInput.fill('1234');
                await profilePage.createCategoryModal.selectIconByIndex(2);
                await profilePage.createCategoryModal.addCategoryButton.click();
            });

            await step('Verify success message and presence of new category in the list', async () => {
                await profilePage.toast.expectSuccess('Category added!');
                const categoryCard = await profilePage.categoriesSection.getCategoryCardByName('Test Category');
                await expect(categoryCard).toBeVisible();
                await expect(categoryCard).toContainText('1234');
            });
        });

        test('User sees validation errors when creating category with empty fields', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            
            await step('Navigate to profile and open add category modal', async () => {
                await profilePage.goto();
                await profilePage.categoriesSection.addNewButton.click();
            });

            await step('Submit empty form', async () => {
                await profilePage.createCategoryModal.addCategoryButton.click();
            });

            await step('Verify required field validation error', async () => {
                await profilePage.expectFieldError('name', 'Enter a category name');
            });
        });

        test('User can delete a category', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            let categoryCard: Locator;

            await step('Navigate to profile and find "Food" category', async () => {
                await profilePage.goto();
                categoryCard = await profilePage.categoriesSection.getCategoryCardByName('Food');
            });

            await step('Initiate category deletion and confirm', async () => {
                await profilePage.categoriesSection.OpenDeleteModalFor('Food');
                await profilePage.confirmDeleteModal.deleteButton.click();
            });

            await step('Verify success message and category removal from UI', async () => {
                await profilePage.toast.expectSuccess('Category deleted');
                await expect(categoryCard).not.toBeVisible();
            });
        });

        test('User can edit a category', async ({ page }) => {
            const profilePage = new ProfilePage(page);
            let categoryCard: Locator;

            await step('Navigate to profile and open edit modal for "Transport" category', async () => {
                await profilePage.goto();
                categoryCard = await profilePage.categoriesSection.getCategoryCardByName('Transport');
                await profilePage.categoriesSection.OpenEditModalFor('Transport');
            });

            await step('Update category details and save', async () => {
                await profilePage.editCategoryModal.nameInput.fill('Updated Transport');
                await profilePage.editCategoryModal.mccCodeInput.fill('5678');
                await profilePage.editCategoryModal.selectIconByIndex(4);
                await profilePage.editCategoryModal.saveChangesButton.click();
            });

            await step('Verify success message and updated details in UI', async () => {
                await profilePage.toast.expectSuccess('Category updated successfully!');
                await expect(categoryCard).toBeVisible();
                await expect(categoryCard).toContainText('Updated Transport');
                await expect(categoryCard).toContainText('5678');
            });
        });
    });
});