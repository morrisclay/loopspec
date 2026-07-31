# What does not compile

- Calibration — nothing scores the estimator's past predictions. No Flue construct; must be built over EventStreamStore.
- Resource — tokens/time/compute budget. Flue has no accounting.
- Uncertainty — Flue has no distribution or confidence type. Estimate carries it as URAS-side state only.
