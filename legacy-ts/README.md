# legacy-ts

The original TypeScript / React / Vite implementation, kept only because the Python parity fixtures in `../tests/parity/fixtures/` were generated from its engine.

- The Python app does **not** need anything in here.
- To regenerate the fixtures (needs [Bun](https://bun.sh); Node is not needed): `bun run engine/tools/gen-parity-fixtures.ts ../tests/parity/fixtures`.
- To run the old app you would need Node or Bun and `bun install` here (`node_modules/` was deleted).
- `ci.yml.old` is the old GitHub Actions workflow.
- Safe to delete once you no longer want to regenerate the fixtures.
