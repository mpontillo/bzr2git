bzr2git
-------

[![Snap Status](https://build.snapcraft.io/badge/mpontillo/bzr2git.svg)](https://build.snapcraft.io/user/mpontillo/bzr2git)

Python script to convert a set of `bzr` branches into a `git` repository.

Development Goals
=================
While there are other tools available to convert `bzr` repositories to `git`
repositories, no tool addressed all of the following requirements:

 * Support for iterative mirroring.
 * Consistent SHA-1 hashes if the tool runs multiple times.
 * Streamlined history (include only "main" branches, such as trunk plus release branches).

Example Configuration File
==========================

This is an example of a configuration file that was used to mirror the MAAS
`bzr` repositories to `git`.

An external process is needed in order to update each source `bzr` repository
before running `bzr2git`.

    # Destination git repository. Should be a bare repository.
    repo: /opt/src/maas/git

    # Temporary work directory. Contents may be deleted.
    workdir: /opt/src/maas/bzr2git

    # Author/committer names to use if not found
    null_author_name: Unknown author
    null_author_email: unknown-author-email@bzr2git.example.com
    null_committer_name: Unknown committer
    null_committer_email: unknown-committer-email@bzr2git.example.com

    branches:
    # Source bzr branches (list of dictionaries). Valid keys:
    # - source: path/to/bzr/repository
    #   branch: git-branch-name
    # The first branch is the "trunk" branch.
     - source: /opt/src/maas/trunk
       branch: master
     - source: /opt/src/maas/2.1
       branch: '2.1'
     - source: /opt/src/maas/2.2
       branch: '2.2'
     - source: /opt/src/maas/2.0
       branch: '2.0'
     - source: /opt/src/maas/1.10
       branch: '1.10'
     - source: /opt/src/maas/1.9
       branch: '1.9'

After `bzr2git` runs, the destination `repo` will contain branches for each
specified source `bzr` branch. An external process is needed to add the
appropriate `git` remote branches. For each `git` remote, the following
command will forcibly overwrite each mirrored branch:

    git push --all --force $REMOTE
