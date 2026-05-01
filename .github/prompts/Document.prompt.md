---
name: Document
description: trigger a full readme rebuild
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

gui_do *is* meant to be data-driven within feature lifecycle considerations, and the methods, classes, and API surface of gui_do/features/data_driven_runtime.py and gui_do/features/feature_lifecycle.py *are* the primary sources of documentation for this readme.

Discard the current section contents of the readme and determine current state of the package API from primary the primary sources, group like concepts and their overall sections together and for sub-sections similarly organize by like concepts. Only include API information from the primary sources unless the reason to use it is that the function it does isn't in the primary sources.  Only show code examples where the point must be understood, and in those examples always ensure that code reflects data-driven and feature lifecycle considerations, how they are used in features, and other gui_do API shown only as absolutely needed.

Follows this format: gui_do as a project name, and then at most a few-sentence higher-level overview in plain English of what the package provides to a developer audience.

After that section will be a table of contents with links to sections as each section's name and for sub-sections does not link to them.  Sections titles include a link underneath them linking back to the top of the table of contents. Sub-sections do not have links. Format the table of contents using indentation for sections and sub-sections.

All following documentation is written from primary sources and follows data-driven and feature lifecycle approaches, and all code examples must follow those as well.  General gui_do API should not generally be included and it should instead be perfectly clear that gui_do is at the base a gui that the feature lifecyle uses, and feature lifecycles are data-driven by a managed overall lifecycle, and all given points revolve around that.  Data-driven with feature lifecycle integration is the primary focus for all text, code, and primary implementation paradigm in all this documentation.

The next section is a overview written in plain English of what the major systems are in the package, from data-driven feature-lifecycle-perspectives, and how they work together with each other for data-driven and feature lifecycle dynamics, and what kind of applications the faculties they provide are best suited for with those considerations in mind.  This overview should be fairly comprehensive and everything that helps primarily developers an audience.

The next section provides a clear and comprehensive tutorial of both data-driven design and feature lifecycle operations and how they are used in gui_do, covering beginner concepts first and then progressing onto more complex usage patterns.  The section also examines how gui_do automatically handling many common functions and provides many common services as abstractions between your code and through its services and down to the pygame base library.  gui_do is implementation "plumbing" and as automatic as possible so you can focus on the specific tasks you need to solve instead of losing time on that plumbing.  Make sure to cover all feature types like DirectFeature for pure graphics drawing that the gui then overlays on top of, and all needed concepts to use the complete faculties the gui_do data-driven-runtime and feature-lifecycle.  Make this tutorial comprehensive and include code examples always drawn from current state of the package for every major concept.  From the table of contents link to this sections major sub-sections, and underneath all those sections have a link back to the top of the table of contents.

The next section should be called "Minimal Runnable Example and Configuration" and have only a code listing which is always generated from the current state information that the title describes.  Must include full "data-driven" code including bootstrap code, with the demo and its features being the reference for that.

And then following that cover the rest of the data-driven-feature-lifecycle API.  Purposely avoid including public API information from gui_do unless it is required for a need data-driven or feature lifecycle doesn't provide.  Subsections should cover their topics from the beginner aspects towards the more advanced aspects.

When documentation is done updating place a github unittest badge for this package at the beginning of the readme.

Do not create any sections not explictly named here, if there is a section that is not named here remove it.
