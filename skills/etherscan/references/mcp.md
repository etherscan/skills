# Etherscan MCP reference

Use this reference to discover the server's current capabilities through MCP. Do not treat this file as a fixed tool inventory or schema snapshot.

## Use this interface when

- An authenticated agent or MCP client needs an Etherscan capability.
- Tool discovery and schema-validated arguments are preferable to constructing direct HTTP requests.
- Diagnosing MCP transport, authentication, schema, or tool-result failures.

## Live authorities

Use the narrowest applicable authority, in this order:

1. The connected server's live `tools/list` response and advertised input schemas for current tool names, descriptions, arguments, and annotations.
2. The current tool result and protocol error for the behavior of a particular call.
3. The [official Etherscan MCP guide](https://docs.etherscan.io/ai/mcp.md) for the production connection and authentication configuration.
4. The exact linked Etherscan endpoint documentation when a tool declares an API mapping or returns an API-backed result.
5. The current [Model Context Protocol specification](https://modelcontextprotocol.io/specification) for transport and protocol semantics.
6. [Etherscan support](https://etherscan.io/contactus?id=11) when the live server and published authorities do not resolve an authentication, billing, availability, or behavior question.

Live discovery overrides remembered or bundled tool names and schemas.

## Discover current behavior

1. Follow the official guide to connect the client to the current production endpoint and configure bearer authentication without exposing the key.
2. Refresh tool discovery and inspect `tools/list`; do not assume a capability exists because it is available through the website, API, or CLI.
3. Select a tool whose current description matches the requested outcome and inspect its complete input schema before constructing arguments.
4. Resolve the target chain using the current tool schema and official chain authority. Do not guess the field name, type, accepted format, or default.
5. Check any declared endpoint mapping for current plan access, chain restrictions, throttling, pagination, and response semantics.
6. Call the tool and evaluate both MCP-level success and the returned content for service- or application-level errors.

## Durable constraints

The official guide currently identifies the production endpoint as:

```text
https://mcp.etherscan.io/mcp
```

Use this bearer-header shape only when the client asks for the raw authentication form:

```text
Authorization: Bearer YourApiKeyToken
```

- Store the credential in the client's secret configuration or an environment variable. Never print, commit, log, or reproduce it.
- Treat transport, connection, authentication, unknown-tool, and input-schema failures as MCP-layer errors.
- Treat errors represented inside returned tool content as tool, Etherscan API, or other backing-service results; a completed MCP call does not guarantee application success.
- Parse content according to the current tool result rather than assuming every tool returns the same envelope.
- Avoid uncontrolled retries and preserve the original error context.
- Treat the MCP surface as read-only unless current tool discovery and official documentation explicitly establish a state-changing capability.
- Require explicit authorization for the exact payload and chain before any state-changing tool call. Do not infer write support from another Etherscan interface.

## If verification fails

- Do not invent a tool, argument, schema, limit, or capability when live discovery is unavailable.
- State whether the unresolved failure is at the connection, authentication, discovery, schema, or backing-service layer.
- Link the official MCP guide or the exact backing endpoint authority the user can check.
- Do not attempt a state-changing call when its current schema, effect, payload, or target chain cannot be verified.
