// =============================================================================
// Cypress E2E Support File
// =============================================================================

// Import commands
import './commands';

// Disable uncaught exception handling for better debugging
Cypress.on('uncaught:exception', (err, runnable) => {
  // Return false to prevent Cypress from failing the test
  return false;
});

// Log test name before each test
beforeEach(() => {
  cy.log(`Running: ${Cypress.currentTest.title}`);
});
