---
name: hierarchy
description: Describe when to use this prompt
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

We are going to do an overhaul which may be major but is much more likely to be minor on the file and folder structure of the gui_do library.

For file and folder layout organize first by logical function or manager kind and then by types and what subtypes what in folders within the manager kinds, so that the resulting folder structure is as close to the functional surface and type hierarchy as possible. If there is a conflict between which folder a type should be placed in, either manager or type hierarchy then put the affected item into a common "shared" or appropriately named folder. Update all internal constructs related to the new hierarchy, and ensure that all importing remains relative for internal use inside only the gui_do folder so that the user is able to place it anywhere in their folder hierarchy they desire.
