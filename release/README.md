# Release Instructions.

**Note:** _This should only apply to maintainers when prepare for and publishing a new release._

To create a new release:
1. Edit `pydantic/version.py` to set the new version number.
2. **(If the new version is a new minor or major release)** run `pre-commit run -a usage_docs` to update the usage links in docstrings.
3. Run `pdm run release/make_history.py` to update `HISTORY.md`
4. **Important:** curate the changes in `HISTORY.md`:
 - make sure the markdown is valid; in particular, check text that should be in `code-blocks` is.
 - mark any breaking changes with `**Breaking Change:**`
 - curate the list of pydantic-core updates in the `packaging` section:
   - check the corresponding pydantic-core releases for any highlights to manually add to the history
 - deduplicate the `packaging` entries to include only the most recent version bumps for each package
5. Create a pull request with these changes.
6. Once the pull request is merged, create a new release on GitHub, the tag should be `v{VERSION}`, the title should be `v{VERSION} {DATE}` and the body should contain a copy-paste of the `HISTORY.md` section you prepared previously.
7. Ask someone to approve the release once CI has run.
