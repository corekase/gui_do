---
name: lower_base
description: Describe when to use this prompt
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

We are going to make a fundamental restructuring of gui_do as a library and update the demo for all changes. Make a detailed plan to do the following: we're rebasing all logic currently contained for classes that are subclasses of another class to as-base-as-possible-for-common-functionality. So, for every object that shares a base-class somewhere along the hierarchy for common functionality move that to as close to the base of the class hierarchy as possible for all the subclass differences. This is to keep duplication of code to a minimum as common functionality is handled first in super() calls, and then specific subclasses do their specific difference after the common base.
