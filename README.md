# kural

Open-source voice AI agent framework. Build phone agents with the LLM, speech, and telephony providers of your choice — bring your own keys, run for the cost of a phone number.

> **Status:** Early development. Not yet usable. Star/watch to follow progress.

## Why kural

Voice agents shouldn't be locked behind a single vendor's stack or a per-minute markup. Kural is a thin, hackable Python framework that wires together best-in-class speech, language, and telephony providers — with sane defaults and the freedom to swap any layer.

- **Bring your own keys.** Plug in OpenAI, OpenRouter, Groq, Ollama, vLLM, or any OpenAI-compatible endpoint for the LLM. Same for STT and TTS.
- **Free path exists.** Run with free-tier models (OpenRouter free models, local Whisper, local Kokoro TTS) and a $1/mo phone number.
- **Self-hostable.** Single Python process. Deploy on a $5 VPS, your laptop, or a container.
- **Phone-first.** Twilio telephony integration out of the box; browser audio is supported too.

## Architecture

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

Built on [Pipecat](https://github.com/pipecat-ai/pipecat) — every stage is a swappable frame processor.

## Provider matrix

| Layer | Free / local | Paid (BYOK) |
|-------|--------------|-------------|
| LLM   | Ollama, vLLM, OpenRouter free tier | OpenAI, Anthropic (via OpenRouter), Groq, Together |
| STT   | faster-whisper, Distil-Whisper | Deepgram, AssemblyAI |
| TTS   | Kokoro, Piper | ElevenLabs, Cartesia |
| Phone | — | Twilio (required for PSTN) |

Cheapest production setup: Twilio number ($1/mo) + OpenRouter free model + local Whisper + local Kokoro = call minutes only.

## Quickstart

> Not yet runnable. This section will be filled in as the v1 milestone lands.

```bash
git clone https://github.com/<owner>/kural
cd kural
cp .env.example .env  # fill in keys
pip install -e .
python -m kural.server
```

## Roadmap

Tracked via [bullseye](https://github.com/marcelocantos/bullseye) targets. See `bullseye.yaml` once initialised.

- [ ] v0: Echo agent (caller speaks, agent repeats)
- [ ] v0.1: STT → LLM → TTS pipeline with one provider per layer
- [ ] v0.2: Provider adapters (OpenAI-compatible LLM, multiple STT/TTS)
- [ ] v0.3: Twilio telephony integration
- [ ] v0.4: Configurable agent personas (system prompt, tools)
- [ ] v1.0: Production-ready, documented, examples

## Contributing

Issues and PRs welcome. Project values: minimal surface area, no vendor lock-in, hackable single-process design.

## License

MIT — see [LICENSE](LICENSE).

## Name

*Kural* (குறள்) — Tamil for a brief, dense couplet. The Thirukkural is a classical Tamil work of 1,330 of them. A good voice agent says a lot with few words.
