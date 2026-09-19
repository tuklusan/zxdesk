# Toolchain pins

Maintained by tuklusan.

This directory records the exact build and run tool inputs used by the hosted Ubuntu workflow. Large tools are referenced rather than committed. Every referenced archive or package has a SHA-256 pin in `toolchain.env`.

Pinned tools:

- Pasmo 0.5.5: assembler used for TAP and binary output.
- Fuse 1.6.0: ZX Spectrum emulator used for run validation.
- Xvfb 21.1.12 package: virtual X server used by Fuse.
- scrot 1.10 package: screenshot capture helper.
- upeep80 0.2.0: Z80 optimizer reference for development use.
- Workflow checkout and artifact actions are pinned by commit hash.

Use `verify-sources.sh` to download and verify the source archives. The workflow directly verifies the Pasmo archive before building it and pins the Ubuntu run packages to exact versions.
