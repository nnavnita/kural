# kural

[![CI](https://github.com/nnavnita/kural/actions/workflows/ci.yml/badge.svg)](https://github.com/nnavnita/kural/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-%E2%89%A580%25-brightgreen.svg)](#quality-gates)

**Site:** [nnavnita.github.io/kural](https://nnavnita.github.io/kural)

Open-source voice AI agent framework. Build phone agents with the LLM,
speech, and telephony providers of your choice — bring your own keys, run
for the cost of a phone number.

> **Status:** Early development. v0 echo agent works locally. Star/watch
> to follow progress.

## Why kural

Voice agents shouldn't be locked behind a single vendor's stack or a
per-minute markup. Kural is a thin, hackable Python framework that wires
together best-in-class speech, language, and telephony providers — with
sane defaults and the freedom to swap any layer.

- **Bring your own keys.** Plug in OpenAI, OpenRouter, Groq, Ollama, vLLM,
  or any OpenAI-compatible endpoint for the LLM. Same for STT and TTS.
- **Free path exists.** Run with free-tier models (OpenRouter free
  models, local Whisper, local Kokoro TTS) and a $1/mo phone number.
- **Self-hostable.** Single Python process. Deploy on a $5 VPS, your
  laptop, or a container.
- **Phone-first.** Twilio telephony integration out of the box; browser
  audio is supported too.

## Target architecture

```
Caller → Twilio (PSTN/SIP) → Media stream
                                  ↓
                              [VAD] Silero
                                  ↓
                              [STT] Whisper / Deepgram
                                  ↓
                              [LLM] OpenAI-compatible (any provider)
                                  ↓
                              [TTS] Kokoro / Piper / ElevenLabs
                                  ↓
                              Audio back to caller
```

Built on [Pipecat](https://github.com/pipecat-ai/pipecat) — every stage
is a swappable frame processor.

## How v0 works

Today, kural ships a single end-to-end pipeline: the **echo agent**. It
proves the loop from mic capture to speaker playback works without any
external services.

```
Mic ─▶ LocalAudioTransport.input ─▶ EchoProcessor ─▶ LocalAudioTransport.output ─▶ Speakers
                (InputAudioRawFrame)            (OutputAudioRawFrame)
```

Pipecat distinguishes captured audio (`InputAudioRawFrame`) from playback
audio (`OutputAudioRawFrame`) by type even though the payload is the
same bytes. `EchoProcessor` (`kural/processors/echo.py`) rewraps every
input frame as an output frame; every other frame passes through
unchanged. This is the only custom logic in v0 — everything else is a
direct use of Pipecat's `LocalAudioTransport` and `WorkerRunner`.

Module map:

| File | Purpose |
|------|---------|
| `kural/config.py` | `Settings` dataclass, loaded from env / `.env` |
| `kural/processors/echo.py` | `EchoProcessor` frame translator |
| `kural/pipeline.py` | `build_local_transport`, `build_echo_pipeline` |
| `kural/server.py` | `run_echo`, CLI entry (`main`) |

## Provider matrix (future milestones)

| Layer | Free / local | Paid (BYOK) |
|-------|--------------|-------------|
| LLM   | Ollama, vLLM, OpenRouter free tier | OpenAI, Anthropic (via OpenRouter), Groq, Together |
| STT   | faster-whisper, Distil-Whisper | Deepgram, AssemblyAI |
| TTS   | Kokoro, Piper | ElevenLabs, Cartesia |
| Phone | — | Twilio (required for PSTN) |

Cheapest production setup: Twilio number ($1/mo) + OpenRouter free model
+ local Whisper + local Kokoro = call minutes only.

## Quickstart

```bash
# macOS prereq for local audio (PyAudio):
brew install portaudio
# Debian/Ubuntu prereq:
sudo apt-get install -y portaudio19-dev

git clone https://github.com/nnavnita/kural
cd kural
cp .env.example .env            # v0 needs no API keys
python -m venv .venv && source .venv/bin/activate
pip install -e .

kural                           # or: python -m kural.server
```

Wear headphones to avoid a feedback loop, then speak — you should hear
yourself back. Stop with `Ctrl+C`.

### Configuration

`Settings.from_env` reads:

| Variable | Default | Meaning |
|----------|---------|---------|
| `KURAL_SAMPLE_RATE` | `16000` | Audio sample rate (Hz). 16 kHz matches Whisper/Silero. |
| `KURAL_LOG_LEVEL`   | `INFO`  | loguru level (`DEBUG`, `INFO`, `WARNING`, ...). |

Additional variables for later milestones (LLM/STT/TTS/Twilio) are
documented in `.env.example`.

## Development

```bash
pip install -e '.[dev]'

ruff check .                    # lint
ruff format --check .           # formatter
pytest                          # tests + coverage gate
```

`pytest` runs the full suite and fails if line coverage drops below
**80%** (configured in `pyproject.toml`). Coverage is currently 100%.

## Quality gates

Every change must land via a pull request. CI
(`.github/workflows/ci.yml`) enforces, on Python 3.14:

- `ruff check .` lint
- `ruff format --check .` formatting
- `pytest` (all tests pass)
- `--cov-fail-under=80` coverage threshold

Direct pushes to `main` are blocked by the branch protection rules
documented in [CONTRIBUTING.md](CONTRIBUTING.md#branch-protection-repo-admins).

## Roadmap

Tracked via [bullseye](https://github.com/marcelocantos/bullseye) targets
in `bullseye.yaml`.

- [x] v0: Echo agent (mic → speaker passthrough)
- [ ] v0.1: STT → LLM → TTS pipeline with one provider per layer
- [ ] v0.2: Provider adapters (OpenAI-compatible LLM, multiple STT/TTS)
- [ ] v0.3: Twilio telephony integration
- [ ] v0.4: Configurable agent personas (system prompt, tools)
- [ ] v1.0: Production-ready, documented, examples

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome — please run the
local quality gates before pushing.

## License

MIT — see [LICENSE](LICENSE).

## Name

*Kural* (குறள்) — Tamil for a brief, dense couplet. The Thirukkural is a
classical Tamil work of 1,330 of them. A good voice agent says a lot
with few words.
