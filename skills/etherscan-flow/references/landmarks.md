# Etherscan Flow — Known landmarks and scam patterns

> Part of the `etherscan-flow` skill. Read this when labeling CEX / mixer / bridge landmarks (chainid 1 only) or recording `_meta.patterns`. Every Hard rule, the 100-call budget, and the validation rules in `SKILL.md` apply here unchanged.

## Known landmark addresses — Ethereum mainnet (chainid 1) only

**These labels apply ONLY when `chainid == 1`.** A 20-byte address is chain-specific: the same address on BSC, Polygon, Arbitrum, Base, etc. is almost always a *different* entity (or unused), so applying an Ethereum label there would falsely brand an unrelated address as Binance/Coinbase/Tornado and prematurely stop a trace.

- **chainid == 1:** match against the table below. A hit is authoritative — assign the landmark role and stop the branch if it's a CEX/mixer/bridge.
- **chainid != 1:** do **not** use this table at all. Identify CEX/mixer/bridge/router entities on other chains **only from a `nametag` hit** (Step 2), which is Etherscan-curated. If no nametag resolves, leave the address `unknown_*` and add a `chain_landmark_unknown` note to `_meta.gaps` — never carry an Ethereum label across chains.
- **Never treat `getsourcecode` `ContractName` as a landmark.** It is attacker-controlled: anyone can verify a contract under the name `Binance: Hot Wallet 14` and thereby stop your trace at their own address and have it labelled `cex_deposit` (Hard rule 4). `ContractName` may inform `notes` as an uncertain hint only; it must never assign a role or stop a branch.

```
0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b → Tornado Cash: Router
0x722122dF12D4e14e13Ac3b6895a86e84145b6967 → Tornado Cash: Proxy
0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc → Tornado Cash 0.1 ETH Pool
0x47CE0C6eD5B0Ce3d3A51fdb1C52DC66a7c3c2936 → Tornado Cash 1 ETH Pool
0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF → Tornado Cash 10 ETH Pool
0xA160cdAB225685dA1d56aa342Ad8841c3b53f291 → Tornado Cash 100 ETH Pool
0x7F367cC41522cE07553e823bf3be79A889debe1B → OFAC-sanctioned Tornado relayer (EOA)
0x28C6c06298d514Db089934071355E5743bf21d60 → Binance Hot Wallet 14
0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549 → Binance Hot Wallet
0xdFd5293D8e347dFe59E90eFd55b2956a1343963d → Binance 7
0x56Eddb7aa87536c09CCc2793473599fD21A8b17F → Binance 8
0x9696f59E4d72E237BE84fFD425DCaD154Bf96976 → Binance Cold Wallet
0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8 → Binance Cold Wallet 2
0xEB2629a2734e272Bcc07BDA959863f316F4bD4Cf → Coinbase
0xa9D1e08C7793af67e9d92fe308d5697FB81d3E43 → Coinbase 10
0x77134cbC06cB00b66F4c7e623D5fdBF6777635EC → Coinbase
0x503828976D22510aad0201ac7EC88293211D23Da → Coinbase 2
0x236F233dBf030fD63F9CF8c08Da5e7bd4ed14F55 → OKX Hot Wallet
0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b → OKX 2
0xf89d7b9c864f589bbF53a82105107622B35EaA40 → Bybit Hot Wallet
```

**Maintaining this table.** A hit here assigns `mixer_contract`/`cex_deposit`, halts the branch, and — for the Tornado rows — carries a sanctions implication into a document that reads as Etherscan-grounded evidence. A wrong row therefore brands an innocent contract. Never add or edit a row from memory. Verify first, on-chain, and record how:

- Tornado ETH pools expose `denomination()` (`0x8bca6d16`). `eth_call` it: the returned wei must equal the labelled denomination. Tornado has exactly four ETH pools — 0.1, 1, 10, 100. **There is no 1000 ETH pool.** The Router and Proxy have no `denomination()`.
- For every other row, require a `nametag` hit (Step 2) and confirm the address is live with `eth_getCode` / `balance`. `getsourcecode` `ContractName` may be recorded only as corroborating context after identity is established; it is never sufficient to add, label, or retain a landmark.
- A row that cannot be verified does not go in the table. Leave the address `unknown_*` and let Step 2 classify it.

---

## Common scam patterns to call out

When any of these are found, add an entry to `_meta.patterns` (e.g. `{"pattern": "approval_drain", "evidence_txhash": "0x..."}`) — never as chat text:

- **Approval drain**: victim called `approve()`, attacker called `transferFrom()`
- **Flash loan attack**: large borrow from Aave/Compound/dYdX in same block as drain
- **Rug pull**: liquidity removed from DEX pair by contract owner shortly after launch
- **Wash trading**: same address sending tokens back and forth to itself or closely linked address
- **Rapid scatter**: attacker splits funds to 5+ sub-wallets within 10 blocks
- **Mixer usage**: any hop routes through Tornado Cash or known mixer
- **Bridge hop**: funds sent to a bridge (cross-chain laundering)
- **CEX fast deposit**: funds reach a CEX deposit within 100 blocks of the drain

---
