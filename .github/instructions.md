-   Do not create or modify any .md files besides updating the wiki.md
-   Keep wiki.md concise and scannable
-   Focus wiki on essentials: quick start, commands, configuration, test instructions

## Command & Environment Guidelines

-   ALWAYS verify venv is active before running commands
-   This project uses Windows PowerShell v5.1 (not bash)
-   Use semicolons (;) to join multiple commands on one line for PowerShell
-   Activate venv with: `.\.venv\Scripts\Activate.ps1`
-   Escape PowerShell special characters appropriately ($ ` | etc)
-   Avoid bash/linux-only commands (use `echo` not `cat`)
-   When showing terminal commands, test them first in PowerShell
-   Confirm commands work with the project's make target wrappers
