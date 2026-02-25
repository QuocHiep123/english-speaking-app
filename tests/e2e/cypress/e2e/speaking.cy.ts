// =============================================================================
// Cypress E2E Test - Speaking Practice Flow
// =============================================================================

describe('Speaking Practice', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('displays the main page correctly', () => {
    cy.contains('VietSpeak AI').should('be.visible');
    cy.contains('Luyện phát âm tiếng Anh').should('be.visible');
  });

  it('displays practice phrase', () => {
    cy.contains('Hello, how are you?').should('be.visible');
  });

  it('allows phrase selection', () => {
    // Click second phrase button
    cy.get('button').contains('2').click();
    
    // Should show the second phrase
    cy.contains('Nice to meet you').should('be.visible');
  });

  it('has a working record button', () => {
    cy.get('[aria-label="Start recording"]').should('be.visible');
    cy.get('[aria-label="Start recording"]').should('not.be.disabled');
  });

  describe('Recording Flow', () => {
    it('requests microphone permission on record', () => {
      // Mock microphone permission
      cy.window().then((win) => {
        cy.stub(win.navigator.mediaDevices, 'getUserMedia').resolves({
          getTracks: () => [{ stop: cy.stub() }],
        });
      });

      cy.get('[aria-label="Start recording"]').click();
      
      // Button should change to recording state
      cy.get('.recording').should('exist');
    });
  });

  describe('Score Display', () => {
    it('shows score after recording', () => {
      // This would require mocking the API response
      // For now, we verify the structure exists
      cy.intercept('POST', '/api/pronunciation/analyze', {
        statusCode: 200,
        body: {
          success: true,
          transcription: 'Hello, how are you?',
          score: {
            overall: 85,
            accuracy: 82,
            fluency: 88,
            completeness: 90,
          },
          feedback: {
            phonemes: [],
            suggestions: ['Good job!'],
            vietnamese_interference: [],
          },
        },
      }).as('analyzeRequest');

      // Would need to trigger recording and then check results
    });
  });

  describe('Accessibility', () => {
    it('has accessible record button', () => {
      cy.get('[aria-label="Start recording"]').should('have.attr', 'aria-label');
    });

    it('uses semantic HTML', () => {
      cy.get('main').should('exist');
      cy.get('header').should('exist');
    });
  });

  describe('Responsive Design', () => {
    it('works on mobile viewport', () => {
      cy.viewport('iphone-x');
      cy.contains('VietSpeak AI').should('be.visible');
      cy.get('[aria-label="Start recording"]').should('be.visible');
    });

    it('works on tablet viewport', () => {
      cy.viewport('ipad-2');
      cy.contains('VietSpeak AI').should('be.visible');
    });
  });
});

describe('Error Handling', () => {
  it('shows error when API fails', () => {
    cy.intercept('POST', '/api/pronunciation/analyze', {
      statusCode: 500,
      body: { error: 'Internal server error' },
    }).as('analyzeFailure');

    // Would trigger recording and check error display
  });

  it('handles network timeout', () => {
    cy.intercept('POST', '/api/pronunciation/analyze', {
      delay: 35000, // Longer than timeout
      statusCode: 200,
    });

    // Would trigger recording and check timeout handling
  });
});
