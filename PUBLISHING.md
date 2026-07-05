# Publishing sm-resolver to PyPI

`sm-resolver` publishes via **PyPI Trusted Publishing** — no API tokens. You tell
PyPI once that this repo's `release.yml` workflow may publish; after that, pushing
a version tag builds and uploads automatically.

## One-time setup (≈5 minutes — this is the part only you can do)

1. Sign in to PyPI (the same account that publishes the rest of the `sm-*` family).
2. Go to **https://pypi.org/manage/account/publishing/** → "Add a pending
   publisher" (use *pending*, because the `sm-resolver` project doesn't exist on
   PyPI yet — the first publish creates it).
3. Fill the form with **exactly** these values:

   | Field | Value |
   |-------|-------|
   | PyPI Project Name | `sm-resolver` |
   | Owner | `Sharathvc23` |
   | Repository name | `sm-resolver` |
   | **Workflow name** | `release.yml`  ← just the filename |
   | Environment name | *(leave blank)* |

That's it. No secret is created or stored anywhere.

## Releasing (every time, after setup)

```bash
# bump `version` in pyproject.toml + update CHANGELOG, commit, then:
git tag v0.1.0
git push origin v0.1.0
```

The `release` workflow builds the sdist + wheel, runs `twine check`, and uploads
to PyPI over OIDC. Watch it under the repo's **Actions** tab. Within a minute,
`pip install sm-resolver` works for everyone.

## Notes

- The tag (`v0.1.0`) and `version` in `pyproject.toml` must match.
- Dry run anytime, no upload: `python -m build && python -m twine check dist/*`.
- Making this public also unblocks `sm-divergence`'s CI, which depends on this
  package (a private dependency otherwise needs a PAT to clone in Actions).
