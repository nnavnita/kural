# kural

[![CI](https://github.com/nnavnita/kural/actions/workflows/ci.yml/badge.svg)](https://github.com/nnavnita/kural/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-%E2%89%A580%25-brightgreen.svg)](#quality-gates)

**Site:** [nnavnita.github.io/kural](https://nnavnita.github.io/kural)

Open-source voice AI agent framework. Build phone agents with the LLM,
speech, and telephony providers of your choice — bring your own keys, run
for the cost of a phone number.

> **Status:** Early development. v0.1 voice agent (STT → LLM → TTS)
> works locally; telephony (inbound/outbound calls via Twilio) is wired
> up; echo agent still available for transport smoke tests.
> Star/watch to follow progress.

## Why kural

Voice agents shouldn't be locked behind a single vendor's stack or a
per-minute markup. Kural is a thin, hackable Python framework that wires
together best-in-class speech, language, and telephony providers — with
sane defaults and the freedom to swap any layer.

- **Bring your own keys.** Plug in OpenAI, OpenRouter, Groq, Ollama, vLLM,
  or any OpenAI-compatible endpoint for the LLM. Same for STT and TTS.
- **Free path exists.** Run with free-tier models (OpenRouter free
  models, local Whisper, local Piper TTS) and a $1/mo phone number.
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
                              [TTS] Piper / Kokoro / ElevenLabs
                                  ↓
                              Audio back to caller
```

Built on [Pipecat](https://github.com/pipecat-ai/pipecat) — every stage
is a swappable frame processor.

## How it works today

kural ships three modes, switchable via `KURAL_MODE`:

**`voice` (default)** — the v0.1 cascade:

```
Mic ─▶ input ─▶ Whisper STT ─▶ user_aggregator ─▶ LLM ─▶ Piper TTS ─▶ output ─▶ Speakers
                                       (Silero VAD)                          │
                                                                              ▼
                                                              assistant_aggregator
```

Silero VAD lives inside the user aggregator and decides when the caller
has stopped speaking; the LLM uses an OpenAI-compatible endpoint, so any
provider (OpenAI, OpenRouter, Ollama, vLLM, …) drops in via env vars.

**`echo`** — the v0 passthrough used as a transport smoke test:

```
Mic ─▶ input ─▶ EchoProcessor ─▶ output ─▶ Speakers
                (InputAudioRawFrame → OutputAudioRawFrame)
```

`EchoProcessor` (`kural/processors/echo.py`) rewraps every input frame
as an output frame so the same bytes can flow to the speaker sink. This
is the only custom logic in echo mode — everything else is a direct use
of Pipecat's `LocalAudioTransport` and `WorkerRunner`.

**`telephony`** — runs a FastAPI/uvicorn server instead of a local audio
loop. Inbound calls hit a webhook, get bridged onto a Twilio Media
Streams WebSocket, and run through the *same* `build_voice_pipeline` as
`voice` mode — only the transport differs (`FastAPIWebsocketTransport`
instead of `LocalAudioTransport`). Each call is its own `PipelineWorker`,
so multiple calls run concurrently. A small REST API
(`POST /calls/outbound`, `GET /calls`, `GET /calls/{sid}`) places
outbound calls and reads call history from a local SQLite log:

```
                        POST /telephony/voice (webhook)
Caller ─▶ Twilio ─────────────────────────────────────▶ TwiML <Connect><Stream>
                        WS  /telephony/media/{call_sid}
       ◀──────────────────────────────────────────────▶ build_voice_pipeline(...)
```

The Twilio integration is one `TelephonyAdapter` implementation
(`kural/adapters/twilio_tel.py`) behind the same registry pattern as the
LLM/STT/TTS adapters — Pipecat already ships serializers for Telnyx,
Plivo, Exotel, Genesys, and Vonage, so adding another provider is a new
adapter class, not a pipeline change. Requires `KURAL_PUBLIC_BASE_URL`
(a publicly reachable host — `ngrok http 8000` for local dev) plus
`TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER`. See
`.env.example`.

Module map:

| File | Purpose |
|------|---------|
| `kural/config.py` | `Settings` dataclass, loaded from env / `.env` |
| `kural/processors/echo.py` | `EchoProcessor` frame translator |
| `kural/services.py` | STT / LLM / TTS service factories |
| `kural/pipeline.py` | `build_local_transport`, `build_echo_pipeline`, `build_voice_pipeline` |
| `kural/server.py` | `run`, `select_pipeline`, `run_telephony`, CLI entry (`main`) |
| `kural/adapters/twilio_tel.py` | `TwilioTelephonyAdapter` — webhook, TwiML, media serializer, outbound dial |
| `kural/telephony/app.py` | FastAPI app: webhook, media-stream WS, outbound/history REST API |
| `kural/telephony/store.py` | SQLite call log (start/end, history) |
| `kural/telephony/registry.py` | In-memory active-call tracking |

### Latency budget (voice mode)

Target on a recent Apple Silicon laptop, all local: **< 2 s** end-to-end
round trip (caller stops speaking → first audio of reply heard).
Rough budget:

| Stage | Budget | Notes |
|-------|--------|-------|
| VAD endpointing | ~250 ms | Silero start/stop windows |
| STT (Whisper distil-medium.en) | ~400 ms | Per utterance, batched |
| LLM (small local model) | ~800 ms | First-token latency dominates |
| TTS (Piper) | ~400 ms | First audio chunk |
| Audio I/O + scheduling | ~150 ms | Buffering, sample-rate conversion |

Swapping the LLM to a hosted provider (OpenAI, Groq) usually shaves
hundreds of milliseconds off the LLM stage. Cloud STT (Deepgram) reduces
STT latency at the cost of bringing your own keys.

## Provider matrix (future milestones)

| Layer | Free / local | Paid (BYOK) |
|-------|--------------|-------------|
| LLM   | Ollama, vLLM, OpenRouter free tier | OpenAI, Anthropic (via OpenRouter), Groq, Together |
| STT   | faster-whisper, Distil-Whisper | Deepgram, AssemblyAI |
| TTS   | Piper, Kokoro | ElevenLabs, Cartesia |
| Phone | — | Twilio (required for PSTN) |

Cheapest production setup: Twilio number ($1/mo) + OpenRouter free model
+ local Whisper + local Piper = call minutes only.

## Quickstart

```bash
# macOS prereq for local audio (PyAudio):
brew install portaudio
# Debian/Ubuntu prereq:
sudo apt-get install -y portaudio19-dev

git clone https://github.com/nnavnita/kural
cd kural
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Voice mode (the default) needs an LLM endpoint. The cheapest local path:

```bash
# 1. Run a small model locally with Ollama (one-time):
ollama pull llama3.1:8b
ollama serve

# 2. Point kural at it:
export KURAL_LLM_BASE_URL=http://localhost:11434/v1
export KURAL_LLM_API_KEY=ollama        # ignored by Ollama; any string
export KURAL_LLM_MODEL=llama3.1:8b

kural                                  # or: python -m kural.server
```

Whisper and Piper auto-download model weights on first run (~1 GB
total). Wear headphones, speak, hear the reply. Stop with `Ctrl+C`.

To run the v0 echo agent (no API keys, no model downloads):

```bash
KURAL_MODE=echo kural
```

### Configuration

`Settings.from_env` reads:

| Variable | Default | Meaning |
|----------|---------|---------|
| `KURAL_MODE`         | `voice`            | `voice` (STT→LLM→TTS) or `echo` (mic passthrough). |
| `KURAL_SAMPLE_RATE`  | `16000`            | Audio **input** rate (Hz). 16 kHz matches Whisper/Silero. |
| `KURAL_OUTPUT_SAMPLE_RATE` | `24000`       | Audio **output** rate (Hz). Higher than input so TTS playback is less choppy. |
| `KURAL_LOG_LEVEL`    | `INFO`             | loguru level (`DEBUG`, `INFO`, `WARNING`, ...). |
| `KURAL_LLM_BASE_URL` | _(OpenAI default)_ | OpenAI-compatible LLM endpoint (Ollama, OpenRouter, vLLM, …). |
| `KURAL_LLM_API_KEY`  | _(unset)_          | API key for the LLM endpoint. |
| `KURAL_LLM_MODEL`    | `gpt-4o-mini`      | Model identifier passed to the provider. |
| `KURAL_STT_MODEL`    | `distil-medium.en` | faster-whisper model id. |
| `KURAL_TTS_VOICE`    | `en_US-amy-medium` | Piper voice id (see [piper-tts voices](https://github.com/rhasspy/piper-tts)). |
| `KURAL_AGENT_PROMPT` | _(built-in)_       | System prompt seeded into the LLM context. |

Additional variables for later milestones (Twilio, recording, …) are
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
- [x] v0.1: STT → LLM → TTS pipeline with one provider per layer
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
