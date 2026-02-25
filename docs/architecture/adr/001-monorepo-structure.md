# ADR-001: Monorepo vs Polyrepo

## Status
**Accepted**

## Context
We need to decide on the repository structure for VietSpeak AI, which consists of multiple components: frontend, backend, AI core, MCP server, and infrastructure.

## Decision Drivers
- Team size (small team, 1-3 developers)
- Component interdependencies (shared types, configs)
- Deployment complexity
- Code review process

## Considered Options

### Option 1: Monorepo with Turborepo
- All components in single repository
- Shared tooling and configurations
- Atomic commits across services

### Option 2: Polyrepo
- Separate repositories per service
- Independent deployment cycles
- Clear ownership boundaries

## Decision
**Monorepo with Turborepo**

## Rationale
1. **Small team**: Single repo reduces context switching
2. **Shared types**: TypeScript types shared between frontend/MCP
3. **Atomic changes**: Breaking changes across services in single PR
4. **Simplified CI/CD**: Single pipeline with component filtering
5. **Research project**: Faster iteration, easier for portfolio review

## Consequences

### Positive
- Single source of truth
- Easier refactoring across components
- Simplified dependency management

### Negative
- Larger repository size
- Requires Turborepo knowledge
- All components share same git history

## Related
- Turborepo documentation
- ADR-003 for MCP integration considerations
