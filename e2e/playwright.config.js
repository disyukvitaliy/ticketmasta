const {defineConfig} = require('@playwright/test');

module.exports = defineConfig({
    testDir: './tests',
    timeout: 60000,
    expect: {timeout: 10000},
    workers: 1,
    reporter: [['list'], ['html', {open: 'never'}]],
    use: {
        browserName: 'chromium',
        baseURL: 'http://localhost',
        actionTimeout: 10000,
        navigationTimeout: 15000,
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure'
    }
});
