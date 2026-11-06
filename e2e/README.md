# End-to-end tests

## Install

On macOS, from this directory:

```sh
brew install node # Includes npm
npm install
npx playwright install chromium
```

## Run

With the development environment running and migrations applied, from this directory:

```sh
npm test
npm test -- --headed # Show the browser
```

## Simulate traffic

Repeat the user journey to generate simple traffic. Workers control concurrency;
each run creates a new account.

```sh
npm test -- --repeat-each=20 --workers=1
```
