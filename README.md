bzr2git
-------
Python script to convert a set of `bzr` branches into a `git` repository.


Development Goals
=================
While there are other tools available to convert `bzr` repositories to `git`
repositories, no tool addressed all of the following requirements:

 * Support for iterative mirroring.
 * Consistent SHA-1 hashes if the tool runs multiple times.
 * Streamlined history (include only "main" branches, such as trunk plus release branches).
