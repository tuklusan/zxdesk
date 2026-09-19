# Toolchain pins

Maintained by tuklusan.

The hosted runner is only a transport host. Build and run steps execute inside the immutable Ubuntu image identified by `EXECUTION_IMAGE` in `toolchain.env`.

Package dependency resolution is frozen to `UBUNTU_SNAPSHOT`. The principal run packages and Pasmo are downloaded from fixed references and checked against SHA-256 values before installation or use. Dependencies selected by the package manager come from the fixed signed Ubuntu snapshot.

Pinned inputs:

- Ubuntu execution image by registry digest.
- Ubuntu package snapshot timestamp.
- Pasmo 0.5.5 source archive.
- Fuse 1.6.0 package and source archive.
- Xvfb package and source archive.
- scrot package and source archive.
- upeep80 0.2.0 source archive.
- Workflow checkout and artifact actions by commit hash.

`install-pinned.sh` installs the build and run environment. `verify-sources.sh` verifies every separately referenced archive and principal package.

The workflow has no timer, push, or review trigger. It can only be started explicitly through the manual workflow dispatch control.
