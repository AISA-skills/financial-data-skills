# KOL Creator Discovery

**AIsa-powered creator email lookup and similar-KOL research.**

Give the skill a TikTok, Instagram, or YouTube creator profile. It looks up the creator's available contact email, discovers similar YouTube or TikTok creators through WaveInflu, enriches every recommended profile with another email lookup, and returns an outreach-ready Markdown table plus optional JSON.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI,
OpenClaw, Hermes, Goose, and others.

Requires Python 3, `curl`, and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## What Can You Do?

### Find a creator's email

```text
"Find the contact email for this Instagram creator profile."
```

### Build a similar-creator list

```text
"Find 15 YouTube creators similar to this channel and include their emails."
```

### Apply campaign filters

```text
"Find US and UK TikTok creators in this content direction with 10K–500K followers."
```

## Quick Start

```bash
export AISA_API_KEY="your-aisa-api-key"

python3 scripts/kol_creator_discovery.py research \
  "https://www.youtube.com/@mkbhd" \
  --limit 10 \
  --out kol-report.md \
  --json-out kol-report.json
```

## Inputs and Outputs

- **Input:** one creator profile URL plus optional platform, content direction, geography, language, follower, average-view, and result-count filters.
- **Output:** a Markdown report and optional JSON containing the seed creator, similar creators, profile links, similarity and audience metrics, emails, and lookup status.

## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
