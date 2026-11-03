# Upload the complete FFI companion repository

1. Extract the final `.tar.gz` archive.
2. Open the extracted `FFI-TESS-Compact-Pulsating-Stars` folder.
3. Create a GitHub repository with that name. Choose Public when ready, but
   leave automatic README, .gitignore and license creation OFF/None: this
   source tree already includes them.
4. Click **uploading an existing file** or **Add file → Upload files**.
5. Upload the **contents** of the extracted folder, not only the compressed
   archive and not an extra enclosing folder.
6. Include hidden `.github/` and `.gitignore` entries. On Linux file managers,
   Ctrl+H commonly shows hidden files; on macOS Finder, Command+Shift+period.
7. Commit with `Initial TESS FFI source upload`.

The repository root should show `README.md`, `pyproject.toml`, `src`, `assets`,
`examples` and `tests` directly. The banner is already linked in the README.
No wheel, extracted `.dist-info`, FITS cache or virtual environment is required.

## Git alternative: NEW EMPTY remote

Open a terminal inside the extracted folder and replace YOUR_USERNAME:

```bash
git init -b main
git add .
git commit -m "Initial TESS FFI source upload"
git remote add origin https://github.com/YOUR_USERNAME/FFI-TESS-Compact-Pulsating-Stars.git
git push -u origin main
```

Authentication must already be configured. For a repository with existing
commits, clone it first, copy the files into that clone, then commit and push
normally. Do not force-push merely to upload this bundle.

This is a prepared release candidate, not an automatic public deployment.
Finish VALIDATION.md before advertising validated performance.
