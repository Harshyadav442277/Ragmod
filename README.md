# Ragmod

Token-efficient RAG, powered by [Paritok](https://paritok.com).

Ragmod is a retrieval-augmented generation app that routes LLM traffic through Paritok's context compression proxy — so you keep answer quality while cutting input tokens.

> Built for **[Build with Paritok: The Token-Efficiency Hackathon](https://build-with-paritok.devpost.com/)**.

## Status

Early scaffold. Clone, open a PR, ship features.

## Quick start

```bash
git clone https://github.com/shreshth006/Ragmod.git
cd Ragmod
```

More setup (deps, Paritok proxy, env vars) coming soon.

## Paritok

This project uses [Paritok](https://github.com/Paritok-official/paritok-4b-v1) as a proxy between the agent/RAG stack and the LLM to compress context and reduce input tokens. Production demos should point at Paritok's **hosted GPU** (`use_gpu_server: true`) so savings show on the dashboard.

## Contributing

1. Fork the repo (or use a feature branch if you have write access)
2. Create a branch: `git checkout -b feature/your-thing`
3. Commit and push
4. Open a PR against `main`

## License

Apache License 2.0 — see [LICENSE](LICENSE).
