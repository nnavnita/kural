# kural

Open-source, bring-your-own-key voice AI agent framework. Wires together LLM, STT, TTS, and telephony providers of your choice via Pipecat, so a phone agent costs the price of a phone number, not a per-minute markup.

Never mention Retell or other closed-source competitors in this repo (marketing/positioning is explicitly BYOK-vs-vendor-lockin).

## Stack

- Python 3.14
- [Pipecat](https://github.com/pipecat-ai/pipecat) (frame-processor pipeline)
- Twilio (telephony), FastAPI/uvicorn (telephony mode server)
- Adapter/registry pattern for LLM (OpenAI-compatible any provider), STT (faster-whisper, Deepgram), TTS (Piper, Kokoro, ElevenLabs)

## Setup

```sh
# macOS prereq for local audio (PyAudio):
brew install portaudio
# Debian/Ubuntu:
sudo apt-get install -y portaudio19-dev

git clone https://github.com/nnavnita/kural
cd kural
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Cheapest local run path — Ollama for the LLM, no API keys:
```sh
ollama pull llama3.1:8b && ollama serve
export KURAL_LLM_BASE_URL=http://localhost:11434/v1
export KURAL_LLM_API_KEY=ollama
export KURAL_LLM_MODEL=llama3.1:8b
kural                        # or: python -m kural.server
```
Whisper + Piper auto-download weights on first run (~1GB). No-key smoke test: `KURAL_MODE=echo kural`.

## Modes (`KURAL_MODE`)

- `voice` (default) — local mic → Whisper STT → LLM → Piper TTS → speakers
- `echo` — v0 passthrough, transport smoke test, no API keys/downloads
- `telephony` — FastAPI server, Twilio Media Streams WebSocket, same `build_voice_pipeline` as voice mode, one `PipelineWorker` per call. Needs `KURAL_PUBLIC_BASE_URL` (`ngrok http 8000` for local dev) + Twilio creds.

## Adding a provider

Never touches `services.py`/`pipeline.py`. Implement the Protocol in `kural/adapters/base.py`, register in `kural/adapters/registry.py`, add `Settings` fields in `kural/config.py` if needed, add the pipecat extra to `pyproject.toml`, add the adapter to the parametrized contract test in `tests/test_adapters.py`. Full walkthrough in README's "Adding a provider" section.

## Development

```sh
pip install -e '.[dev]'
ruff check .                    # lint
ruff format --check .           # formatter
pytest                          # tests + coverage gate (fails under 80%, currently 100%)
```

CI (`.github/workflows/ci.yml`) enforces all of the above on Python 3.14. Direct pushes to `main` blocked — every change lands via PR (see `CONTRIBUTING.md`).

## Roadmap

**`bullseye.yaml` is the source of truth** — managed by the bullseye MCP server. Use `bullseye_frontier` (cwd = this repo) for the next unblocked target.

Shipped: v0 echo agent, v0.1 STT→LLM→TTS pipeline, v0.2 provider adapters, v0.3 Twilio telephony. Next: v0.4 configurable agent personas (system prompt, tools), then v1.0 production-ready + docs + examples.
