# Smart Contract Patterns

Use this reference when explaining proxy behavior, privileged controls, asset flows, or difficult Solidity/EVM constructs.

## Proxy and Upgrade Patterns

Resolve proxies on a best-effort basis. Start with explorer metadata and source, then use only the read-only calls permitted by `SKILL.md` to corroborate a known pattern. Record the observed block when available, detect address cycles, and keep the search bounded. A plausible storage value or function name alone is not proof; corroborate it with runtime bytecode, delegatecall behavior, source, or another independent indicator.

Check these common patterns:

- **Transparent/EIP-1967:** read the implementation slot `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` and admin slot `0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103`, then inspect transparent admin routing. Retrieve source for the implementation address. Keep proxy-admin authority separate from application ownership.
- **UUPS:** inspect the EIP-1967 implementation slot, then locate `upgradeTo`, `upgradeToAndCall`, proxiable UUID behavior, and `_authorizeUpgrade` in implementation source. The proxy holds storage even though the implementation contains upgrade logic.
- **Beacon:** read the EIP-1967 beacon slot `0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50` only when the implementation slot is empty, confirm code at the beacon address, and use a read-only `implementation()` call when supported. Retrieve both beacon and current implementation sources and distinguish beacon ownership from application roles.
- **Minimal proxy/clone:** inspect runtime bytecode for an EIP-1167-style embedded implementation address. Confirm code at the target and state whether the clone uses immutable proxy bytecode or additional initialization/state.
- **Diamond/EIP-2535:** use supported read-only loupe functions such as `facets`, `facetAddress`, or `facetFunctionSelectors` when present. Map selectors to facet addresses and retrieve material facet sources. Do not assume every diamond exposes a complete loupe.
- **Custom delegate proxy:** inspect fallback/receive logic, assembly, storage access, and read-only implementation accessors suggested by executable code. Do not guess arbitrary storage slots or label a candidate address as the implementation without corroboration.

If no known pattern is confirmed, report the contract as a possible or unresolved custom proxy and explain exactly what evidence is missing. Do not force it into the nearest standard. If indirection is cyclic, excessively deep, mutable during retrieval, or dependent on unavailable contracts, stop and preserve that ambiguity.

For every resolved pattern, explain which address users call, which address holds storage, which address or facet contains the current logic, how that logic can change, and what evidence supports each conclusion. Also check for initializers replacing constructors.

## Access-control Patterns

Look for:

- `owner`, `Ownable`, `Ownable2Step`, and ownership transfer or renounce behavior.
- Role systems such as `AccessControl`, `DEFAULT_ADMIN_ROLE`, operator roles, guardians, pausers, minters, burners, keepers, and managers.
- Custom modifiers, allowlists, signature authorization, permit flows, and delegated operators.
- Multisig, timelock, governor, or external admin contracts when addresses or interfaces reveal them.

For each privileged capability, identify who can call it, what it can change, and why it matters.

## Asset-flow Patterns

Track:

- Native asset receipts and sends.
- ERC-20 `transfer`, `transferFrom`, `approve`, `safeTransfer`, and `safeTransferFrom`.
- ERC-721/ERC-1155 transfers and receiver callbacks.
- Mints, burns, staking shares, vault shares, rebasing/accounting balances, and escrow ledgers.
- Fee collection, reward distribution, rescue/sweep functions, and treasury recipients.
- External routers, bridges, vaults, pools, or token contracts that receive custody or approvals.

Separate actual custody movement from internal accounting updates.

## External Calls and Trust Boundaries

Inspect:

- Low-level `call`, `delegatecall`, `staticcall`, and assembly.
- Callbacks, hooks, plugins, strategies, modules, routers, or arbitrary target execution.
- Oracle reads and price assumptions.
- Signature verification, replay protection, nonces, domain separators, and chain IDs.
- Reentrancy guards and checks-effects-interactions patterns where relevant to explaining a flow.

State what the contract trusts and whether those dependencies are fixed, role-configurable, or user-supplied.

## Comments and Naming

Use comments and names only as orientation. Confirm behavior from executable code, modifiers, storage writes, emitted events, and external calls.
