import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    specPattern: 'tests/e2e/cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'tests/e2e/cypress/support/e2e.ts',
    fixturesFolder: 'tests/e2e/cypress/fixtures',
    videosFolder: 'tests/e2e/cypress/videos',
    screenshotsFolder: 'tests/e2e/cypress/screenshots',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: false,
    retries: {
      runMode: 2,
      openMode: 0,
    },
  },
  component: {
    devServer: {
      framework: 'next',
      bundler: 'webpack',
    },
    specPattern: 'apps/frontend/**/*.cy.{js,jsx,ts,tsx}',
  },
});
