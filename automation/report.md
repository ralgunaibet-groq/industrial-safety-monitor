# Report: Reliable Confidence Score Parsing

## Problem

The scoping Devin session must output a JSON object with `confidence_score` and `reasoning` fields. Since Devin produces free-form text, the automation must reliably extract this structured data from potentially noisy output.

## Parsing Strategy

The tool uses a multi-layered extraction approach, applied in priority order:

### Layer 1: Structured Output (Highest Priority)

The Devin API supports a `structured_output` field on session responses. The scoping prompt instructs Devin to update this field with the JSON result. If present and valid, it is used directly without any text parsing.

### Layer 2: Targeted Regex Extraction

If structured output is unavailable, the tool scans session messages (newest first) using two regex patterns:

1. **Strict pattern** - Matches the exact expected format: `{"confidence_score": <number>, "reasoning": "<text>"}`. This catches well-formed output.
2. **Relaxed pattern** - Matches any single-level JSON object containing both `confidence_score` and `reasoning` keys. This handles minor formatting variations.

### Layer 3: Code Block Extraction

Devin often wraps JSON in markdown code blocks. The tool extracts content from ` ```json ... ``` ` blocks and validates that the parsed object contains `confidence_score`.

### Layer 4: Full-Text JSON Parse (Fallback)

As a last resort, the entire message text is passed to `json.loads()`. If the message is purely JSON with the expected key, it is accepted.

## Why This Is Reliable

1. **Prompt engineering** - The scoping prompt explicitly instructs Devin to output the exact JSON format, update structured output, and stop working afterward. This maximizes the chance of clean output.
2. **Multiple extraction strategies** - Four independent parsing layers ensure the score is captured regardless of how Devin formats its response.
3. **Reverse message scanning** - Messages are scanned newest-first, so the final answer takes precedence over any intermediate analysis.
4. **Strict validation** - Every parsed object is checked for the `confidence_score` key before being accepted, preventing false positives from unrelated JSON.
5. **Graceful failure** - If no valid result is found after all layers, the tool prints the last few messages for debugging rather than crashing or using a default value.
