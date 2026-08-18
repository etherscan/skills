# CLI Authentication

Use this reference after a trusted `etherscan-cli` installation is available and before API-backed retrieval.

1. Run `etherscan whoami` to check authentication. Do not print environment variables, configuration files, command history, or process arguments while checking.
2. If authentication succeeds, continue without asking for or displaying the API key.
3. If authentication is absent or invalid, recommend persistent login so later reviews can use the CLI without repeated setup. Ask the user to run `etherscan login` in their own interactive terminal and enter the API key only at the CLI prompt, never in chat. Explain that the CLI saves the key locally in plaintext in its user configuration and that the user should protect that file.
4. Use this prompt shape:

   ```text
   etherscan-cli is installed but is not authenticated. For full read-only retrieval now and in later reviews, run `etherscan login` in your own interactive terminal and enter your API key only at the CLI prompt—not in chat. The CLI saves the key locally in plaintext. Tell me when login completes, and I will verify it with `etherscan whoami` and continue.
   ```

5. If the host provides a secure interactive secret-entry handoff that guarantees the key is hidden from the model, transcript, tool arguments, and logs, offer to launch `etherscan login` only after explicit user consent and yield input control to the user. Otherwise, do not invoke the interactive login on the user's behalf.
6. After the user confirms login, run `etherscan whoami` again. Never echo, recover, inspect, or summarize the saved key.
7. If the user declines persistent login, offer a temporary option only when the user can set `ETHERSCAN_API_KEY` through their own terminal or a host-provided secret mechanism. Do not ask for the value in chat and do not pass it with `--api-key` or embed it in a URL. If no secret-safe method is available, state that authenticated retrieval cannot continue.
8. For invalid-key, throttling, or authentication errors, consult https://docs.etherscan.io/common-error-messages. Avoid repeated invalid attempts.
