# Etherscan API reference

Use this reference to discover and validate the current API capability needed for a task. Do not treat this file as a fixed endpoint inventory.

## Use this interface when

- Integrating Etherscan data into an application or service.
- Requiring direct HTTP access, broad capability discovery, or an exact response schema.
- Troubleshooting authentication, request construction, limits, or service-level errors.

## Live authorities

Use the narrowest applicable authority, in this order:

1. The exact endpoint page and its attached OpenAPI operation for parameters, request method, response shape, and endpoint-specific behavior.
2. The [documentation index](https://docs.etherscan.io/llms.txt) to discover the current endpoint page. Use the [full documentation export](https://docs.etherscan.io/llms-full.txt) only when broad cross-page context is necessary.
3. The current [supported chains](https://docs.etherscan.io/supported-chains.md), [rate limits](https://docs.etherscan.io/resources/rate-limits.md), [PRO endpoints](https://docs.etherscan.io/resources/pro-endpoints.md), and [common errors](https://docs.etherscan.io/resources/common-error-messages.md) for shared service restrictions.
4. The [changelog](https://docs.etherscan.io/changelog.md) when observed behavior differs from earlier documentation or examples.
5. [Etherscan support](https://etherscan.io/contactus?id=11) when the published authorities do not resolve an account, billing, availability, or behavior question.

Prefer the exact endpoint page when a general resource and endpoint-specific documentation differ.

## Discover current behavior

1. Translate the requested outcome into documentation search terms such as the target object, operation, and desired result.
2. Search the documentation index and open the most relevant endpoint page; do not infer an endpoint from a remembered `module` or `action`.
3. Inspect the endpoint page and its OpenAPI operation for the current method, path, query parameters, types, required fields, and response examples.
4. Resolve the exact target chain and confirm its current support. Never infer Etherscan support from EVM compatibility.
5. Verify plan access, chain restrictions, throttling, pagination, truncation, and state-changing behavior through the live authorities before constructing the request.
6. Interpret the actual response according to the documented response model and preserve returned error context.

## Durable constraints

Use the API V2 request envelope unless the exact live authority documents a different service or route:

```text
https://api.etherscan.io/v2/api?chainid={chainid}&module={module}&action={action}&{endpoint_parameters}&apikey=YourApiKeyToken
```

- Pass the exact numeric `chainid` required by the selected endpoint.
- Keep API keys in secret configuration or environment variables. Replace any exposed key with `YourApiKeyToken`; never print, commit, log, or reproduce it.
- Treat `status`, `message`, and `result` as Etherscan response fields when present, not as transport success guarantees. Some endpoint families may use a different documented response model.
- Distinguish HTTP or transport failures, authentication failures, validation failures, throttling, and application-level errors.
- Avoid uncontrolled retries. Respect the current shared and endpoint-specific limits discovered from official sources.
- Require explicit authorization for the exact payload and chain before submitting verification, broadcasting a signed transaction, or performing another state-changing operation.

## If verification fails

- Use only the durable guidance above when a live authority cannot be reached.
- Do not guess endpoint names, parameters, defaults, plan access, limits, supported chains, or availability.
- State which detail could not be verified and link the narrowest official authority the user can check.
- Do not execute a state-changing request whose current behavior or target chain cannot be verified.
