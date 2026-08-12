# Etherscan website reference

Use this reference to discover the current interactive website feature for a task. Do not treat this file as a fixed feature or URL inventory.

## Use this interface when

- A person wants to inspect blockchain data interactively.
- The task depends on a browser-only explorer view, export, tracker, utility, or account service.
- The user needs current product guidance or support rather than a programmable interface.

## Live authorities

Use the narrowest applicable authority, in this order:

1. The correct chain-specific explorer and its current navigation, search, and task-specific page.
2. The [Etherscan homepage](https://etherscan.io/) for Ethereum search and current product navigation.
3. The [Etherscan Information Center](https://info.etherscan.com/) for feature instructions, explanations, and frequently asked questions.
4. The [developer documentation](https://docs.etherscan.io/) for API, CLI, MCP, and contract-verification behavior.
5. The current [supported-chain authority](https://docs.etherscan.io/supported-chains.md) when resolving a network or explorer URL.
6. [Etherscan support](https://etherscan.io/contactus) when current navigation and published guidance do not resolve the task.

Treat the live task-specific page as authoritative for current availability and interactive behavior.

## Discover current behavior

1. Resolve the intended chain from an explicit network, explorer domain, URL, or other unambiguous context. Ask when multiple networks remain plausible.
2. Use the correct explorer's search for an address, transaction hash, block, token, contract, or supported name.
3. For a feature or utility, inspect current navigation and site search, then confirm its purpose on the task-specific page or Information Center.
4. Verify prerequisites, wallet interactions, account requirements, network restrictions, exports, and other consequential behavior on the live page before instructing the user.
5. Return the narrowest current page that accomplishes the task, with any material interaction or safety context.

## Durable constraints

- Do not assume an Ethereum page path or feature exists unchanged on another Etherscan-family explorer.
- Do not infer the target chain from an address or transaction-shaped value alone when several networks remain possible.
- Distinguish read-only inspection from wallet connection, signing, approval revocation, verification submission, message publication, transaction broadcasting, or another external write.
- Require explicit authorization before performing or guiding an automated state-changing interaction on the user's behalf.
- Never request a private key, seed phrase, or raw secret. Treat wallet prompts, signatures, approvals, and signed transactions as security-sensitive.
- Confirm the exact domain before asking the user to connect a wallet or submit sensitive data.

## If verification fails

- Do not invent a feature name, page path, supported network, prerequisite, or interactive behavior.
- State which detail could not be confirmed and provide the nearest official navigation, Information Center, documentation, or support entry point.
- Prefer a safe read-only landing page when the exact task page cannot be verified.
- Do not proceed with wallet connection, signing, approval changes, verification, broadcasting, or another write when the page's current behavior or target network is uncertain.
