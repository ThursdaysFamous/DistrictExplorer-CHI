# These workflows do not run. They are here as source material.

GitHub only reads workflows from **`.github/workflows/` at the repository
root**. This directory sits at `sf/.github/workflows/`, so every file in it is
**inert** — nothing here is scheduled, nothing here fires on a push, and
nothing here has ever run in this repository.

They came across with the `sf/` tree when the `DistrictExplorer-SF`
fork was imported (R3, `docs/DEV_PROCESS_ASSESSMENT.md`), and they are kept
because they are the definition of this instance's 7 roster refreshes — the
thing that has to be rewritten, with instance-aware paths, when those refreshes
move into the root `.github/workflows/`.

**Where this instance's refreshes actually run today:** still in the
`ThursdaysFamous/DistrictExplorer-SF` repository, which is still live and
still serving its own domain. That is deliberate. Importing the tree and moving
the automation are separate steps, and running both would open two competing
PRs against the same roster files.

Do not "fix" a path in here expecting it to take effect, and do not delete
these on the grounds that they are dead — they are the input to the migration,
not its leftovers.
