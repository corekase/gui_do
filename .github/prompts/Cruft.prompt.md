---
name: Cruft
description: This command cleans the package of cruft code
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

Say "Beginning package cleanup." Scan the package for unused or not logically necessary variables, methods, classes, and files and remove them.  Scan the package for shims, facades, compatibility layers, and any backwards compatibility constructs. If any are found then remove them.  If the demo needs to be updated for these changes then update the demo.
