# Packaging (optional)

A standalone executable is **not required**; `python -m sahkku` is the supported way to run the app. This is a recipe for those who want one. It has not been run as part of the project's tests.

```sh
pip install pyinstaller
pyinstaller --name sahkku --onefile \
  --collect-all nicegui \
  --add-data "src/sahkku/i18n:sahkku/i18n" \
  src/sahkku/__main__.py
```

On Windows use `;` instead of `:` in `--add-data`. Notes:

- `--collect-all nicegui` is needed because NiceGUI ships its web assets (Quasar, Vue, icon fonts) as package data.
- The package must be installed (`pip install .`) in the environment you build from.
- `--onefile` unpacks to a temporary folder on every start; prefer `--onedir` if start-up time matters.
- The Hard AI uses `multiprocessing`; frozen builds on Windows need `multiprocessing.freeze_support()` at the start of `main()` (not added to the source because the app is not built this way by default).
- Keep `LICENSE` and the notices in `CULTURAL_NOTES.md` with any binary you share, and do not distribute before the checks recommended in `CULTURAL_NOTES.md`.
