# Source Candidate Generator Report

## Implementation

Implemented candidate generation through `generate_source_candidate` in `product/regradar/app/source_discovery.py`.

The generator creates an inactive work-queue compatible source candidate from a discovered endpoint.

## Fields Generated

- `proposed_source_id`
- `regulator`
- `jurisdiction`
- `title`
- `official_url`
- `source_type`
- `discovery_method`
- `adapter_family`
- `adapter_name`
- `adapter_config`
- `expected_min_length`
- `selector_hints`
- `buyer_relevance`
- `noise_risk`
- `source_health_risk`
- `current_state`
- `next_action`
- `source_monitor_gate`
- `evidence_trail_gate`
- `qa_critic_gate`
- `legal_language_gate`
- `product_manager_gate`
- `code_architect_gate`
- `final_activation_gate`

## Safety Decision

Generated candidates are **not** written directly into `sources.json`.

Default state is:

- `current_state: candidate`
- `final_activation_gate.status: candidate`
- `evidence_trail_gate.status: hold`

No generated candidate claims proof, evidence, baseline completion, or monitoring readiness.

## Why This Matters

The generator lets StatuteProof build a high-volume source work queue without polluting the active source registry or inflating public source counts.

