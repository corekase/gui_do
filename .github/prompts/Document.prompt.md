---
name: Document
description: trigger a full readme rebuild
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

Determine current state of the package API, update sections if they already exist otherwise create new sections as needed in the appropriate location of the readme. Group like concepts and their overall sections together and for sub-sections similarly organize by like concepts. Only include public API information in the readme. Only show code examples where the point must be understood, and in those examples always ensure that code is up-to-date with the current state of the API.

Follows this format: gui_do as a project name, and then at most a few-sentence higher-level overview in plain English of what the package provides to a developer audience.

After that section will be a table of contents with links to sections as each section's name and for sub-sections does not link to them.  Sections titles include a link underneath them linking back to the top of the table of contents. Sub-sections do not have links. Format the table of contents using indentation for sections and sub-sections.

The next section provides a clear and comprehensive tutorial of both data driven design and graphic user interface programming, covering beginner concepts first and then progressing onto more complex usage patterns, in the context of how gui_do implements both these paradigms in its internal systems - in the general case, and provides automatic handling of many common functions with gui_do being an abstraction of implementation details so that all the "plumbing" is as automatic as possible so you can focus on the specific tasks you need to solve instead of losing time on the plumbing.  Make sure to cover all feature types like DirectFeature for pure graphics drawing that the gui then overlays on top of and all needed concepts to use the complete faculties gui_do provides.  Make this tutorial comprehensive and include code examples for every major concept, and from the table of contents link to its major sub-sections, this section is the only section with links to sub-sections.

The next section is a overview written in plain English of what the major systems are in the package, how they work together with each other, and what kind of applications the faculties they provide are best suited for.  This overview should be fairly comprehensive and everything that helps primarily developers an audience as end-users aren't likely to be reading package documentation.

The next section should be called "Minimal Runnable Example and Configuration" and have only a code listing which is what the title describes.

And then following that cover the rest of the public API.  Sections should be ordered in the same order you will be typically using them in your own code.  Subsections should cover their topics from the beginner aspects towards the more advanced aspects.

When documentation is done updating place a github unittest badge for this package at the beginning of the readme.
