# Report Rubric

Use this reference as the authoritative output specification. Apply the default template to a general contract review and the narrow-answer rule when the user asks a focused question.

## Default Report Template

```markdown
## Developer Overview

[A few sentences describing the likely role, who uses it, what assets or permissions matter, and what privileged operators can change. Include uncertainty where appropriate.]

## Contract Identity

- Chain:
- User-facing/proxy address:
- Implementation address:
- Verification/compiler metadata:
- Observed at:

## How It Works

### User Flow

[Describe ordinary user entry points, required inputs/approvals, state changes, asset movement, and outputs.]

### Admin and Operator Flow

[Describe privileged entry points, roles, upgrade authority, pausing, configuration, rescue/withdrawal, mint/burn, and emergency actions.]

### Asset Flow

[Describe native/token custody, transfers, accounting, fees, recipients, and external protocols.]

### External Dependencies

[Describe trusted contracts, oracles, routers, tokens, callbacks, and whether addresses are fixed or configurable.]

## Code Map

- Entry points:
- Accounting and state:
- Asset movement:
- Access control:
- Upgradeability:
- External integrations:
- Validation and error handling:
- Libraries and inherited behavior:

## Important Functions, Events, and Storage

[List only material items. Group by responsibility.]

## Evidence and Uncertainty

[Cite source references for material claims. List unresolved questions, missing source, unresolved proxy metadata, or dependencies not reviewed.]

## Limitation

This is a source-code explanation for developer orientation, not a security audit or statement that the contract is safe.
```

## Quality Bar

Ensure the final report:

- Identifies the probable contract role and states uncertainty.
- Separates user actions from privileged actions.
- Covers material asset-moving and privileged functions.
- Keeps proxy and implementation responsibilities separate.
- Cites source file, contract, and function/modifier/event/storage references for important claims.
- Explains Solidity/EVM concepts only when they affect behavior.
- Avoids overclaiming from comments, names, ABI entries, or incomplete metadata.

## Narrow Answers

When the user asks a narrow question, answer directly first, then include the minimum supporting source references and caveats. Do not generate the full report unless it helps answer the question.
