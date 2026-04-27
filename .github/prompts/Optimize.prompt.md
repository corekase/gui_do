---
name: Optimize
description: Describe when to use this prompt
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

We are going to do an optimization pass. Make a plan to analyze the entire package looking for both local and larger-scale logic, code, and systems reorganizations and other improvements measured by performance-first followed by resource efficiency, sensible tests in logic to cull out unneeded iteration of code as needed, and appropriate data structures with the measure being performance-first followed by resource efficiency. If there are significant improvements that could be made but would be a larger structual change then make a subplan for that task, run it, and resume to the caller when it completes. For every task and subtask strict adherence to best patterns and practices for whichever relevant domains must be obeyed. If any structures are found that do not obey best patterns and practices for their domain then correct them so that they do.
