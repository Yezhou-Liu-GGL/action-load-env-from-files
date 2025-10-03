# action-load-env-from-files

Load KEY=VALUE pairs from one or more simple text files into the GitHub Actions environment for subsequent workflow steps.

## Summary

This composite action lets you keep environment variable definitions in versioned files (e.g. `.env.shared`, `deploy.vars`) and load them during a workflow. It parses each specified file, ignoring comments / blank lines, then exports variables for the remainder of the job. Duplicate keys are overridden by later occurrences.

Typical use cases:

* Share a curated set of non‑secret defaults across multiple workflows.
* Prepare environment variables before running build / packaging / deployment scripts.
* Load files generated in a prior step (e.g. templated variable files).

> NOTE: Do NOT store secrets in plain text files. Use GitHub Secrets or a secret manager. The action can mask values, but masking does not make them secret inside the runner.

## Input Parameters

| Name | Required | Description | Default |
| ---- | -------- | ----------- | ------- |
| `files` | Yes | List of files (newline / comma / semicolon separated). Supports `.env` style and `.yml/.yaml` with a root `variables:` map. | (none) |
| `fail-on-missing` | No | Fail the action if any listed file is missing. If `false` missing files are skipped with a warning. | `true` |
| `mask-secrets` | No | Add each loaded value to the mask list to hide it in logs (only enable for sensitive values). | `false` |
| `sanitize-variable-names` | No | Replace invalid shell chars (`[^A-Za-z0-9_]`) in keys with `_` so they can be exported; leading digits get a leading `_`. | `true` |
| `upper-case-variable-names` | No | Convert sanitized names to upper case (e.g. `Version.Major` -> `VERSION_MAJOR`). | `true` |

File parsing rules:
* `.env` / plain text: lines beginning with `#`, `//` or `;` are comments; first `=` separates key and value; value may contain additional `=`.
* YAML (`.yml`, `.yaml`): we look for a top-level `variables:` mapping; its key-value pairs become variables.
* Multi-line YAML block scalars (e.g. `|` style) are preserved as multi-line environment variables.
* Arrays in YAML become newline-joined lists.
* Invalid shell variable characters are replaced with `_` if sanitization enabled.
* Later definitions override earlier ones (merge across files in order provided).
* If the runner PowerShell lacks `ConvertFrom-Yaml` (older pwsh/Windows PowerShell), a fallback lightweight parser is used (supports: simple `variables:` root, flat keys, block `|`, simple lists, no anchors/aliases). For advanced YAML features, ensure the job uses PowerShell 7+.
* Values shorter than 4 characters are not masked (to avoid polluting logs with generic masked tokens); open an issue if you need configurable behavior.

## Output Parameters

| Name | Description | Example |
| ---- | ----------- | ------- |
| `variable-count` | Number of variables loaded. | `6` |
| `variable-names` | Comma separated list of sanitized variable names loaded. | `API_URL,LOG_LEVEL` |
| `variable-map-json` | Compact single-line JSON array mapping `{ "original": "Original.Name", "env": "SANITIZED_OR_NEW_NAME" }`. | `[ {"original":"Version.Major","env":"VERSION_MAJOR"} ]` |
### YAML Example

YAML file `build-variables.yml`:

```yaml
variables:
  Version.Major: 9
  Version.Minor: 40
  VersionFilesPattern: |
    Customisations\**\AssemblyInfo.cs
    Customisations\**\*.csproj
    Elmo\**\AssemblyInfo.cs
    Elmo\**\*.csproj
```

Workflow usage (note sanitized names):

```yaml
    - uses: actions/checkout@v4
    - name: Load vars
      id: load
      uses: GGLSecDev/action-load-env-from-files@v1
      with:
        files: build-variables.yml
    - name: Echo
      run: |
        echo "Major=$VERSION_MAJOR Minor=$VERSION_MINOR"
        echo "Pattern=$VERSIONFILESPATTERN"
        echo "Map=${{ steps.load.outputs.variable-map-json }}" | jq '.'
```


## Example

Assume you have a file `.ci.env`:

```
# Common variables
API_URL=https://api.example.com
LOG_LEVEL=Information
; comment style also supported
FEATURE_FLAG_X=true
```

Workflow usage:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Load vars
        id: load-env
        uses: GGLSecDev/action-load-env-from-files@v1
        with:
          files: |
            .ci.env
            config/runtime.vars

      - name: Show loaded variables
        run: |
          echo "Count=${{ steps.load-env.outputs.variable-count }}"
          echo "Names=${{ steps.load-env.outputs.variable-names }}"
          echo "API_URL=$API_URL"
          echo "LOG_LEVEL=$LOG_LEVEL"
```

## Local Testing

You can test the script locally (PowerShell 7+) by setting the two special files manually:

```powershell
$env:GITHUB_OUTPUT = "$PWD/out.txt"
$env:GITHUB_ENV    = "$PWD/env.txt"
pwsh ./.build/LoadEnvFromFiles.ps1 -Files ".ci.env" -FailOnMissing $true
Get-Content out.txt
Get-Content env.txt
```

## Feedback and contributions

Issues and ideas welcome via GitHub Issues / Discussions. Please coordinate significant changes with the maintainers first.

## Security

Do not commit secrets. Treat any value loaded from a file as non‑secret. For secrets use encrypted GitHub Action secrets or an external secret store.


## Feedback and contributions

Please feel free to contribute by submitting an issue or
[joining the discussions](https://github.com/GGLSecDev/REPO_NAME/discussions/categories/ideas). Each contribution helps
improve our workflows.

Before contributing new features or bug fixes please make sure that you have had a conversation with another developer
on how to best implement the changes you are aiming to make. Ideally this conversation is done in a discussion thread or
a work item so that it is recorded for the future.

## Testing

When fixing a bug or contributing a new feature, we recommend testing the changes against a suitable repository. If you
don't have a specific repository to test against you can use the .NET template repositories, e.g. the
[service template](https://github.com/GGLSecDev/template-service-dotnet) or the
[library template](https://github.com/GGLSecDev/template-library-dotnet).

Include a link to your test runs in your Pull Request to indicate what tests have been run and what the outcome of these
tests was.
