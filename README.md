# Ragmod

[![Built with Paritok](https://img.shields.io/badge/Built%20with-Paritok-1f2d3d)](https://github.com/Paritok-official/paritok-4b-v1)

A retrieval agent for codebases. Ask a question about a repository, get an answer with `file:line` citations.

Retrieval runs through tools, so every chunk of code arrives as a `tool_result` — the content [Paritok](https://github.com/Paritok-official/paritok-4b-v1)'s 4B compressor is trained on. That lets Ragmod retrieve generously and stay cheap: recall goes up, the bill does not.

> Built for **[Build with Paritok: The Token-Efficiency Hackathon](https://build-with-paritok.devpost.com/)**.

## Status

Early scaffold — design is settled, implementation starting.

- [Architecture](docs/ARCHITECTURE.md) — what we're building and why
- [Paritok integration](docs/PARITOK.md) — how compression is wired and measured
- [Build plan](docs/PLAN.md) — waves, ownership, deadline
- [Critique](docs/CRITIQUE.md) — what the first design got wrong

## Quick start

```bash
git clone https://github.com/shreshth006/Ragmod.git
cd Ragmod
```

More setup (deps, Paritok proxy, env vars) coming soon.

## Paritok

Built with [Paritok](https://github.com/Paritok-official/paritok-4b-v1). Every LLM call leaves through the Paritok proxy running against the **hosted GPU** (`use_gpu_server: true`), which compresses tool results, accumulated history, and unused tool schemas before the request reaches the provider. See [docs/PARITOK.md](docs/PARITOK.md) for the wiring and the measurement method.

## Contributing

1. Fork the repo (or use a feature branch if you have write access)
2. Create a branch: `git checkout -b feature/your-thing`
3. Commit and push
4. Open a PR against `main`

## License

Apache License 2.0 — see [LICENSE](LICENSE).
