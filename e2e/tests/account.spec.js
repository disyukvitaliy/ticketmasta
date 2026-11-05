const {randomUUID} = require('node:crypto');
const {test, expect} = require('@playwright/test');

test('register, confirm, log in, and view the profile', async ({page}) => {
    const email = `e2e-${randomUUID()}@example.com`;
    const password = 'E2e-password-123!';

    await test.step('Register through the browser', async () => {
        await page.goto('/register');
        await page.getByLabel('Email', {exact: true}).fill(email);
        await page.getByLabel('Password', {exact: true}).fill(password);
        await page.getByLabel('Confirm Password', {exact: true}).fill(password);
        await page.getByLabel('I accept the terms').check();
        await page.getByRole('button', {name: 'Register', exact: true}).click();
        await expect(page.getByRole('heading', {name: 'Check your email'})).toBeVisible();
    });

    await test.step('Read the confirmation email and follow its link', async () => {
        let messageId;
        await expect.poll(async () => {
            const query = encodeURIComponent(`to:${email}`);
            const response = await fetch(`http://localhost:8025/api/v1/search?query=${query}`);
            expect(response.ok).toBeTruthy();
            const result = await response.json();
            messageId = result.messages[0]?.ID;
            return messageId;
        }, {timeout: 20000, message: 'Confirmation email should arrive in Mailpit'}).toBeTruthy();

        const response = await fetch(`http://localhost:8025/api/v1/message/${messageId}`);
        expect(response.ok).toBeTruthy();
        const message = await response.json();
        expect(message.Subject).toBe('Confirm your email');
        const confirmationUrl = message.Text.match(/http:\/\/localhost\/confirmation\?token=[\w-]+/)[0];

        await page.goto(confirmationUrl);
        await expect(page.getByText('Email confirmed.', {exact: true})).toBeVisible();
    });

    await test.step('Log in through the browser', async () => {
        await page.getByRole('link', {name: 'Login', exact: true}).click();
        await page.getByLabel('Email', {exact: true}).fill(email);
        await page.getByLabel('Password', {exact: true}).fill(password);
        await page.getByRole('button', {name: 'Login', exact: true}).click();
        await expect(page).toHaveURL('http://localhost/');
    });

    await test.step('Verify the profile after Kafka events are consumed', async () => {
        await page.getByRole('link', {name: 'Profile', exact: true}).click();
        await expect(page).toHaveURL('http://localhost/profile');

        await expect.poll(async () => {
            await page.reload();
            return page.getByLabel('Notification email').inputValue();
        }, {timeout: 20000, message: 'Profile should contain the confirmed notification email'}).toBe(email);

        await expect(page.getByText(/^Profile ID: \d+$/)).toBeVisible();
        await expect(page.getByLabel('First name')).toHaveValue('');
        await expect(page.getByLabel('Last name')).toHaveValue('');
    });
});
