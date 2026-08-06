# Etherscan Flow — Performance and adaptive rate control

> Read this before the first API data call on every run. It defines query reuse, evidence waves, pagination, and rate handling. Hard rules and data-integrity requirements in `SKILL.md` always win over speed.

## Work profile

The 100-call and 20-page limits are safety ceilings, not targets. Select a profile without asking:

| Profile | Selection | Soft call target | Initial pagination |
|---------|-----------|------------------|--------------------|
| `standard` | Default | 40 new calls | Pages 1–2, then widen active unresolved branches |
| `fast` | User asks for quick/preliminary results | 25 new calls | Page 1, then only evidence-required widening |
| `deep` | User asks for exhaustive/full/deep work, or complete totals require it | 80 new calls | Progressively widen relevant branches toward the hard ceiling |

Soft targets may be crossed for required edge validation or completion of an active high-value branch. Record the reason in `_meta.performance.soft_budget_overrun_reason`. Never cross 100 actual network attempts.

## Canonical query ledger

Before planning calls, create an in-memory ledger keyed by `(transport, chainid, module, action, canonical parameters excluding apikey)`.

- Normalize address/txhash case for the key, sort parameters, and normalize numeric strings.
- Load matching `case-{SHORT_ID}-fetchlog.jsonl` rows before making calls.
- Check the ledger before every request. Cache/fetch-log hits cost no API call.
- Store raw response, fetch time, attempt count, and elapsed milliseconds.
- Maintain a movement index keyed by `(chainid, txhash, logIndex|traceId|top-level)`. Receipt logs are canonical for event movements; account feeds may enrich them but not duplicate them.

## Fetch log — persist as you fetch, resume for free

The ledger's on-disk twin. Append each raw API response as one line of `case-{SHORT_ID}-fetchlog.jsonl` in the scratchpad/temp directory:

```json
{"module": "...", "action": "...", "params": {}, "chainid": 1, "fetched_at": "ISO", "result": null}
```

- **Strip `apikey` from `params` before writing** (Hard rule 6).
- Append the row inside the same transport/tool operation that fetched the response whenever the runtime allows it. Never spend a separate model/tool round trip just to log.
- When a run with the same seed starts and this file exists, **load it first**: answer every already-logged call from the log, and continue from the first missing call.
- Replayed calls do not count against the 100-call budget; only new network calls do. Count them in `_meta.performance.fetchlog_hits`.

This is what makes an interruption — rate limit, provider safety flag, model switch, crash — cost nothing but the relaunch.

## Evidence waves

Plan and execute the smallest next evidence wave, update the graph, then plan again:

1. **Seed:** transaction, receipt and internals; or minimum address-entry scans.
2. **Primary evidence:** parse held logs/rows and identify only unresolved metadata and surviving endpoints.
3. **Classification:** one batched nametag request plus targeted classification of surviving nodes.
4. **Trace:** initial pages for active branches, stop terminals, progressively widen unresolved branches.
5. **Totals:** reuse trace pages and fetch only missing continuation pages.
6. **Incident analysis (security cases):** reason over held evidence, then fetch only state/source/log evidence that can resolve a material mechanism or competing hypothesis.
7. **Validation:** validate from held responses; fetch only evidence missing for a surviving edge or required analysis claim.

Independent requests in one wave should share one grouped/parallel tool call when supported. Never launch the entire remaining budget at once because later calls may become unnecessary.

## Adaptive rate handling

Never hard-code requests per second. Effective limits vary by API key, plan, endpoint, and transport.

1. Prefer limits or retry guidance exposed by the transport/response; honor `Retry-After`.
2. Without a signal, begin with a small bounded wave and increase concurrency only after success.
3. Keep calls concurrent only while the transport succeeds; preserve dependencies between waves.
4. On a rate-limit response, pause that endpoint family, reduce the next wave, and retry at most once.
5. Count every network attempt against the 100-call ceiling; cache hits do not count.
6. Record a second failure once in gaps, skip it, and continue where evidence permits.

MCP or CLI may throttle internally. Do not add a conflicting fixed sleep.

## Pagination and reuse

- Use `offset=100` consistently for `txlist` and `tokentx` trace/totals queries so Step 3 pages can be reused in Step 3B.
- Stop on a short page. Widen only active, non-terminal branches whose last page was full or points farther into the window.
- Do not query/paginate token standards absent from held evidence.
- Stop high-volume and terminal landmark addresses; do not enumerate them merely to consume the allowance.
- Business totals may require full relevant pagination, but must reuse every compatible ledger page.

## Required metrics

Add `_meta.performance` to every case with: `profile`, `new_api_calls`, `network_attempts`, `cache_hits`, `fetchlog_hits`, `retries`, `rate_limit_responses`, `pages_fetched`, `pages_reused`, `soft_call_target`, `hard_call_limit`, `elapsed_ms`, `stage_elapsed_ms` (`seed`, `classification`, `trace`, `totals`, `analysis`, `validation`), and `soft_budget_overrun_reason`. Never include credentials.
