# CLI Installation Fallback

Use this reference only when a trusted `etherscan` executable is unavailable on `PATH`. Do not execute a same-named binary discovered only in the current working directory.

1. Detect the operating system, architecture, and active shell without asking the user when they are available from the environment. Check read-only whether relevant package managers or runtimes are already available; do not install prerequisites implicitly.
2. Read the live **Install** section of https://github.com/etherscan/etherscan-cli/ immediately before offering installation. Treat the repository as authoritative for supported operating systems, architectures, installation channels, prerequisites, and commands.
3. Present a numbered menu containing only the repository's installation methods applicable to the detected OS. Label missing prerequisites, distinguish persistent installations from one-shot methods such as `npx`, and include a final option to decline installation and use the Etherscan API directly. Do not collapse the menu into a yes/no prompt.
4. Show the exact command or repository-prescribed manual procedure for every option. Preserve command spelling, arguments, URLs, shell, ordering, and verification steps exactly as documented; do not translate commands between shells or substitute an unofficial package manager.
5. Include the chain, contract address, and intended continuation in the prompt when known. Use this shape:

   ```text
   etherscan-cli is not available. I detected <OS/architecture/shell>.
   May I install etherscan-cli and then continue the <chain> review of <address>?
   Select one option:
   1. <applicable method> — <exact repository command(s)>
   2. <applicable method> — <exact repository command(s)>
   ...
   N. Do not install — use the Etherscan API directly.
   ```

6. Wait for the user's selection. Execute only the selected repository-prescribed command after explicit consent. Treat pipe-to-shell, package-manager, `go install`, archive download, and `PATH` changes as installation actions requiring that consent. Request separate consent before installing any missing prerequisite.
7. Run the repository's documented verification command after installation. If the repository says a new terminal is required for `PATH` changes, explain that and retry from an appropriate fresh shell when possible. Do not claim installation succeeded until verification succeeds.
8. After verification succeeds, return to `SKILL.md` and follow `references/cli-authentication.md`. Installation success does not imply that API authentication is configured.
