---
name: Document
description: Describe when to use this prompt
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

Determine current state of the package API, update sections if they already exist otherwise create new sections as needed in the appropriate location of the readme. Group like concepts and their overall sections together and for sub-sections similarly organize by like concepts. Only include public API information in the readme. Only show code examples where the point must be understood, and in those examples always ensure that code is up-to-date with the current state of the API.

Follows this format: gui_do as a project name, and then at most a few-sentence higher-level overview in plain English of what the package provides to a developer audience.

After that section will be a table of contents links to sections and lists but does not link to sub-sections.  Sections titles include a link on their right side linking back to the top of the table of contents. In each section title there is another link to the right of the section title "Back to Top" which links back to the top of the table of contents. Sub-sections do not have links. Format the table of contents using indentation for sections and sub-sections.

The next section is a quick start section.

The next section is an overview section written in plain English of what the major systems are in the package, how they work together with each other, and what kind of applications the faculties they provide are best suited for.  This overview should be fairly comprehensive and everything that helps primarily developers an audience as end-users aren't likely to be reading package documentation.

The next section should be called "Minimal Runnable Example" and have only a code listing which is what the title describes.

Follow that with a "Package Management" section with "Start a New Project" and "Add to or Update an Existing Project" sub-sections that detail the usage of the scripts/manage.py tool.

And then following that cover the rest of the public API.  Sections should be ordered in the same order you will be typically using them in your own code.  Subsections should cover their topics from the beginner aspects towards the more advanced aspects.

When documentaion is done updating place a github unittest badge for this package at the beginning of the readme.
