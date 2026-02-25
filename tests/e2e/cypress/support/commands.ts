// =============================================================================
// Cypress Custom Commands
// =============================================================================

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Mock microphone permission
       */
      mockMicrophone(): Chainable<void>;

      /**
       * Record audio for specified duration
       */
      recordAudio(durationMs: number): Chainable<void>;

      /**
       * Wait for pronunciation analysis to complete
       */
      waitForAnalysis(): Chainable<void>;
    }
  }
}

Cypress.Commands.add('mockMicrophone', () => {
  cy.window().then((win) => {
    const mockStream = {
      getTracks: () => [
        {
          stop: () => {},
          kind: 'audio',
        },
      ],
    };

    cy.stub(win.navigator.mediaDevices, 'getUserMedia').resolves(mockStream);
  });
});

Cypress.Commands.add('recordAudio', (durationMs: number) => {
  cy.get('[aria-label="Start recording"]').click();
  cy.wait(durationMs);
  cy.get('[aria-label="Stop recording"]').click();
});

Cypress.Commands.add('waitForAnalysis', () => {
  cy.get('[data-testid="loading-indicator"]').should('not.exist');
  cy.get('[data-testid="score-display"]').should('be.visible');
});

export {};
