# Release Instructions.

**Note:** _This should only apply to maintainers when prepare for and publishing a new release._

## Prerequisites:
* `gh` cli is installed - see installation instructions [here](https://docs.github.com/en/github-cli/github-cli/quickstart)
  * Run `gh auth login` to authenticate with GitHub, which is needed for the API calls made in the release process.
* Repository has all tags from previous releases.
  * If your repository is a fork, you may need to fetch tags from the upstream repository:
  * Run `git remote add upstream https://github.com/pydantic/pydantic.git` if you haven't already.
  * Run `git fetch upstream --tags` to fetch all tags from the upstream repository.

## Simi-automated Release Process:

1. Run `uv run release/prepare.py {VERSION}` from the root of the repository. This will:
    * Update the version number in the `version.py` file.
    * Add a new section to HISTORY.md with a title containing the version number tag and current date.
    * If you just want to see the effect of the script without making any changes, you can add the `--dry-run` flag.
2. Curate the changes in number.md:
   - make sure the markdown is valid; in particular, check text that should be in `code-blocks` is.
   - mark any breaking changes with `**Breaking Change:**`
   - curate the list of pydantic-core updates in the `packaging` section:
     - check the corresponding pydantic-core releases for any highlights to manually add to the history
   - deduplicate the `packaging` entries to include only the most recent version bumps for each package
3. Run `uv run release/push.py` from the root of the repository. This will:
    * Create a PR with the changes you made in the previous steps.
    * Add a label to the PR to indicate that it's a release PR.
    * Open a draft release on GitHub with the changes you made in the previous steps.
4. Review the PR and merge it.
5. Publish the release and wait for the CI to finish building and publishing the new version.

## Manual Release Process

To create a new release:
1. Edit `pydantic/version.py` to set the new version number and run `uv lock -P pydantic`
2. Run `uv run release/make_history.py` to update `HISTORY.md` and `CITATION.cff`.
3. **Important:** curate the changes in `HISTORY.md`:

4. Create a pull request with these changes.
5. Once the pull request is merged, create a new release on GitHub:
   - the tag should be `v{VERSION}`
   - the title should be `v{VERSION} {DATE}`
   - the body should contain:
     - a copy-paste of the `HISTORY.md` section you prepared previously, plus
     - a full changelog link in the form `Full Changelog: https://github.com/pydantic/pydantic/compare/v{PREV_VERSION}...v{VERSION}/`
6. Ask @sydney-runkle, @samuelcolvin, or @dmontagu to approve the release once CI has run.
