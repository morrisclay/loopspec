# Relation-vocabulary proposal

Evidence base: 700 resolved edges in 23 encodings across 9 domains, queried from
`ALL_EDGES.json` and `ASSERTS_CANDIDATES.json` with Python. Counts below are corpus counts,
not counts inferred from the YAML. YAML references identify the original node or edge lines.

## Verdict on the current 15

| relation | keep / merge / split / drop | evidence |
|---|---|---|
| `measures` | **split** | Only `Signal -> Estimand` has one stable meaning (57 edges). The other uses are different roles: 11 `Estimator -> Signal`, 4 `Party -> Signal`, and one reversed `Signal -> Estimator` (`OBSERVED_USAGE.md:23-27`). The thermostat makes the category error explicit: `hallway_temp -> room_comfort` is measurement, while `hallway_temp -> passthrough` is estimator input, yet both are called `measures` (`encodings/thermostat__claude.yaml:103-111`). Keep `measures` only for `Signal -> Estimand`; migrate the others to `reads`, `asserts`, or `observes`. |
| `estimates` | **split** | It conflates process output (`Estimator -> Estimate`, 42), an estimate's subject (`Estimate -> Estimand`, 21), and a shortcut from process to subject (`Estimator -> Estimand`, 14) (`OBSERVED_USAGE.md:18-21`). In one file, `supplier_judgement -> supplier_delivery_estimate` and `supplier_delivery_estimate -> motor_arrival_by_need_date` use the same verb for two different edges in one chain (`encodings/factory__gpt-5-codex.yaml:229-243`). Retype the first role to `produces` and the second to `about`; reject or expand the 14 shortcuts into the full chain. |
| `holds` | **split** | The 106 `Party -> {Estimate, DesiredCondition, PreferenceOrdering}` edges coherently attach an attitude to a party. The six `Estimate -> Estimand` edges do not: they duplicate the `Estimate -> Estimand` branch of `estimates`. Compare `launch_reliability_estimate -> launch_reliability` labelled `holds` (`encodings/spacex__deepseek-v3.2.yaml:141-146`) with the same structural role labelled `estimates` elsewhere (`encodings/factory__gpt-5-codex.yaml:241-249`). Keep the Party branch; merge the six outliers into `about`. |
| `targets` | **keep** | Forty-nine of 50 uses are exactly `DesiredCondition -> Estimand`. The sole `Intervention -> Resource` use is not a second meaning worth preserving: ordering motors increases motor inventory and should be `replenishes` (`encodings/factory__gpt-5-codex.yaml:129-151,298-300`). |
| `closes` | **split, then retire** | It is six relations hiding under one token: `Loop -> Intervention` (15), `Policy -> Intervention` (13), `Intervention -> Loop` (10), `Loop -> TimeScale` (6), `Loop -> Signal` (6), and `Loop -> Revision` (1) (`OBSERVED_USAGE.md:37-43`). The opposite orientations alone disqualify a single invariant. Worse, `loops[]` already records timescale, signal, and intervention (`uras.graph.md:65-69`); Toyota repeats those fields as three `closes` edges and then repeats them again in `loops[]` (`encodings/toyota__gemini-2.5-pro.yaml:213-245`). Delete loop-membership `closes` edges as redundant. Merge `Policy -> Intervention` with the identical branch of `authorizes` into `governs`. |
| `delays` | **split** | `Delay -> Signal/Intervention` says a lag delays an outcome (12 edges); `Intervention -> Delay` says an action incurs or has a lag (10 edges). Those are not the same direction or role. The contrast is visible between `issue_po -> lead_time_delay` (`encodings/factory__deepseek-v3.2.yaml:202-204`) and `supplier_lead_time -> supplier_portal_status` (`encodings/factory__gpt-5-codex.yaml:164-166,319-321`). Keep `delays` for `Delay -> affected node`; use `incurs` for `Intervention -> Delay`. |
| `constrains` | **keep, with bad edges removed** | The coherent core has `Constraint` as source: 22 `Constraint -> Intervention`, 3 `Constraint -> Revision`, 3 `Constraint -> Estimand`, and 1 `Constraint -> Policy`. The two `Intervention -> Resource` edges are resource effects, not constraints (`OBSERVED_USAGE.md:52-57`): postponing a discretionary plan preserves energy (`encodings/family__gpt-5-codex.yaml:118-133,270-272`), while a TAC regulates a fish stock (`encodings/ecosystem__gpt-5-codex.yaml:96-106,219-224`). |
| `authorizes` | **split** | `Party/System -> Intervention` is actual authority: the thermostat controller is deliberately a `System`, not a `Party`, but holds actuation authority (`encodings/thermostat__claude.yaml:50-53,127-129`). `Policy -> Intervention` is a decision mapping and duplicates `closes`: 7 edges use `authorizes`, 13 use `closes` for the same kind pair. For example, three factory policies “authorize” actions (`encodings/factory__deepseek-v3.2.yaml:184-192`), while the thermostat policy “closes” its action (`encodings/thermostat__claude.yaml:136-138`). Both should be `governs`. The two `Party -> Constraint` edges mean `imposes`, not authorizes. |
| `consumes` | **keep, but audit every use** | All 39 edges have the right nominal signature, `Intervention -> Resource`, but kind agreement conceals false semantics. `discharge -> beds` cannot consume an available bed; it frees one (`encodings/hospital__claude.yaml:286-288`). `reduce_hiring -> cash` preserves cash rather than consuming it (`encodings/portfolio_company__claude.yaml:141-152`). A tether test is said to retain the vehicle but is still encoded as consuming it (`encodings/hop_aero__gpt5codex.yaml:251-265`). Keep only literal stock decrease. |
| `revises` | **split** | The coherent core is a `Revision` or own-structure `Intervention` changing a schema-bearing node, e.g. `standardized_work_revision -> standardized_work` (`encodings/toyota__gpt5codex.yaml:230-232`). Three uses are different: a Party initiates a Revision (`line_worker -> revise_standard_work`, `encodings/toyota__gemini-2.5-pro.yaml:195-200`), a Calibration calibrates an Estimator (`encodings/venture_acme__claude.yaml:143-146,193-195`), and installing an andon enables a future Signal (`encodings/toyota__claude.yaml:179-182,333-335`). Retype them to `initiates`, `calibrates`, and `enables`. |
| `contains` | **keep** | Its six allowed pairs all express structural inclusion or membership, not causal action: `System -> Boundary`, `Boundary -> Party`, `System -> Loop/Party/System/Policy` (`OBSERVED_USAGE.md:29-35`). This is legitimate typed polymorphism if the allowed pair matrix is explicit. Do not infer physical containment or transitivity across every pair. |
| `bears` | **keep** | This is the cleanest relation in the corpus: all 79 uses are `Party -> Consequence` (`OBSERVED_USAGE.md:9-10`), and the relation is constitutive of Party (`uras.graph.md:119-120`). |
| `asserts` | **keep** | The zero count is a migration failure, not absence of evidence. Three existing `Party -> Signal` edges are reports or responses forced into `measures`: `air_force -> procurement_feedback` (`encodings/hop_aero__deepseek-v3.2.yaml:141-143`), `suppliers -> supplier_response` (`encodings/spacex__deepseek-v3.2.yaml:132-134`), and `supervisor -> quality_report` (`encodings/toyota__deepseek-v3.2.yaml:154-156`). The fishery encoding independently states that reported landings are assertions by regulated parties under economic pressure and that the missing reporting-party relation is the defect (`encodings/ecosystem__gpt-5-codex.yaml:270-277`). |
| `replenishes` | **keep** | At least two existing resource edges have the wrong polarity: `order_buffered_motors -> motors` is labelled `targets` (`encodings/factory__gpt-5-codex.yaml:298-300`), and `discharge -> beds` is labelled `consumes` (`encodings/hospital__claude.yaml:286-288`). Both increase the available stock. Toyota also has a `replenish` intervention and a parts resource but no edge between them (`encodings/toyota__claude.yaml:164-166,220-225`), while another Toyota encoding states the exact signal-to-replacement mapping in a note (`encodings/toyota__gpt5codex.yaml:127-129`). |
| `produces` | **keep only with a new definition** | The held-out artifact justification is not instantiated: the encoding says semantic artifacts need production, consumption, and translation, but does not contain artifact nodes or production edges (`encodings/llm_agent_system__gpt-5-codex.yaml:361-369`). There is nevertheless overwhelming corpus evidence for `Estimator -> Estimate`: 42 edges in 19 encodings currently misuse `estimates`, e.g. `demand_estimator -> e_demand` (`encodings/venture_acme__claude.yaml:163-165`) and `passthrough -> comfort_est` (`encodings/thermostat__claude.yaml:106-108`). Keep `produces` for that evidenced signature. Do not claim the unevidenced `System/Intervention -> Signal` signature is validated. |

The answer to question 1 is therefore **no**. Only `bears` and `contains` need no edge
migration. `targets`, `constrains`, and `consumes` keep their names only after bad edges are
ejected; `holds` and `revises` retain a core after splitting; the other five in-use relations
need semantic replacement or normalization. Even the single-signature `consumes` contains
obvious polarity errors.

## Re-typings required

These are concrete edge migrations, not hypothetical examples. Pattern totals come from the
resolved JSON; representative edge citations make each pattern auditable.

| file | from | to | currently | should be | why |
|---|---|---|---|---|---|
| `hop_aero__deepseek-v3.2.yaml:141` | `air_force` | `procurement_feedback` | `measures` | `asserts` | A customer/procurement party authors feedback; it does not measure a Signal. |
| `spacex__deepseek-v3.2.yaml:132` | `suppliers` | `supplier_response` | `measures` | `asserts` | Supplier response is party-authored and filtered, not a measurement act. |
| `toyota__deepseek-v3.2.yaml:154` | `supervisor` | `quality_report` | `measures` | `asserts` | This is the corpus's cleanest report edge. |
| `toyota__deepseek-v3.2.yaml:151` | `line_worker` | `observed_defect` | `measures` | `observes` | Direct observation is the negative control: authorship without the report/claim semantics of `asserts`. |
| `factory__gpt-5-codex.yaml:298` | `order_buffered_motors` | `motors` | `targets` | `replenishes` | Ordering 10,500 motors increases motor inventory. |
| `hospital__claude.yaml:286` | `discharge` | `beds` | `consumes` | `replenishes` | Discharge releases an occupied bed into available stock. |
| `ecosystem__gpt-5-codex.yaml:162` | `stock_assessment_model` | `assessment_ssb` | `estimates` | `produces` | An estimator produces an estimate. Apply this rule to all 42 `Estimator -> Estimate` edges in 19 encodings. |
| `factory__gpt-5-codex.yaml:229` | `supplier_judgement` | `supplier_delivery_estimate` | `estimates` | `produces` | Same `Estimator -> Estimate` production role. |
| `thermostat__claude.yaml:106` | `passthrough` | `comfort_est` | `estimates` | `produces` | Same role even for a degenerate identity estimator. |
| `venture_acme__claude.yaml:163` | `demand_estimator` | `e_demand` | `estimates` | `produces` | Same role in the held-out venture encoding. |
| `ecosystem__gpt-5-codex.yaml:174` | `assessment_ssb` | `true_spawning_stock_biomass` | `estimates` | `about` | An Estimate is about an Estimand; it does not perform estimation. Apply to all 21 edges of this pair. |
| `hop_aero__deepseek-v3.2.yaml:150` | `vehicle_performance_estimate` | `vehicle_performance` | `holds` | `about` | Same `Estimate -> Estimand` role, proving `holds` and `estimates` duplicate each other here. Apply to all six such `holds` edges. |
| `spacex__deepseek-v3.2.yaml:141` | `launch_reliability_estimate` | `launch_reliability` | `holds` | `about` | Same duplicate role in a second domain. |
| `ecosystem__deepseek-v3.2.yaml:110` | `stock_assessment_model` | `survey_catch_data` | `measures` | `reads` | The estimator consumes a Signal as input. Apply to all 11 `Estimator -> Signal` edges. |
| `factory__deepseek-v3.2.yaml:148` | `gut_feeling_estimator` | `supplier_portal_status` | `measures` | `reads` | Same input role. |
| `thermostat__claude.yaml:109` | `hallway_temp` | `passthrough` | `measures` | `reads` **and reverse** | Normalize to `passthrough -> hallway_temp`; it is the same input role encoded backwards. |
| `factory__deepseek-v3.2.yaml:184` | `material_check_policy` | `issue_po` | `authorizes` | `governs` | Policy selects/guards an action; it is not an authority-bearing party. |
| `thermostat__claude.yaml:136` | `bang_bang` | `fire_boiler` | `closes` | `governs` | Same `Policy -> Intervention` role under a second label. Apply `governs` to all 20 such edges across 13 encodings. |
| `ecosystem__deepseek-v3.2.yaml:146` | `set_tac` | `one_year_delay` | `delays` | `incurs` | The intervention has/incurs a delay; the Delay is not what it delays. |
| `factory__deepseek-v3.2.yaml:202` | `issue_po` | `lead_time_delay` | `delays` | `incurs` | Same role. Apply to all 10 `Intervention -> Delay` edges across 7 encodings. |
| `hop_aero__deepseek-v3.2.yaml:198` | `regulator` | `licensing_constraint` | `authorizes` | `imposes` | A regulator imposes a licensing constraint. |
| `spacex__deepseek-v3.2.yaml:186` | `regulators` | `safety_constraint` | `authorizes` | `imposes` | Same role in a second aerospace encoding. |
| `family__gpt-5-codex.yaml:270` | `postpone_discretionary_plan` | `parent_energy` | `constrains` | `preserves` | Postponement conserves attention/recovery capacity. |
| `portfolio_company__claude.yaml:150` | `reduce_hiring` | `cash` | `consumes` | `preserves` | A runway-preservation action reduces cash outflow. |
| `ecosystem__deepseek-v3.2.yaml:143` | `set_tac` | `fish_stock` | `consumes` | `regulates` | Setting a quota regulates removals; it does not itself catch fish. |
| `ecosystem__gpt-5-codex.yaml:219` | `set_and_allocate_tac` | `cod_stock` | `constrains` | `regulates` | Same resource-regulation role under another forced label. |
| `hop_aero__gpt5codex.yaml:251` | `conduct_tether_test` | `test_vehicles` | `consumes` | `risks` | The node's motive says the tether test retains the vehicle; consumption states the opposite. |
| `toyota__gemini-2.5-pro.yaml:198` | `line_worker` | `revise_standard_work` | `revises` | `initiates` | The Party initiates/performs the Revision; it does not revise the Revision node. |
| `venture_acme__claude.yaml:193` | `demand_calibration` | `demand_estimator` | `revises` | `calibrates` | The source node is explicitly a Calibration whose note says it scores this estimator. |
| `toyota__claude.yaml:333` | `install_andon` | `andon_pull` | `revises` | `enables` | Installing the apparatus enables future andon signals; it does not revise a particular signal datum. |
| `toyota__gemini-2.5-pro.yaml:213` | `andon_loop` | `timescale_minutes` | `closes` | delete | The adjacent `loops[]` entry already supplies this exact role (`:240-245`). |
| `hop_aero__gpt5codex.yaml:275` | `conduct_tether_test` | `tether_learning_loop` | `closes` | delete | The edge is backwards relative to 15 `Loop -> Intervention` uses and duplicates `loops[]`. |

The three orphan decisions required by question 2 are therefore:

- **Keep `asserts`**, with the three concrete `measures -> asserts` migrations above.
- **Keep `replenishes`**, with `order_buffered_motors -> motors` and `discharge -> beds`.
- **Keep and redefine `produces`**, migrating the 42 `Estimator -> Estimate` edges. If the
  definition is not changed from `System/Intervention -> Signal`, then drop it: that declared
  signature has no corpus instance.

## Test of the `asserts` prediction

The narrow prediction—“the need is not confined to fishery reporting”—is true. The resolved
candidate set contains only four `Party -> Signal` edges, and three are plausible assertions
in three encodings:

1. Air Force procurement feedback (`encodings/hop_aero__deepseek-v3.2.yaml:141-143`).
2. Supplier response (`encodings/spacex__deepseek-v3.2.yaml:132-134`).
3. Supervisor quality report (`encodings/toyota__deepseek-v3.2.yaml:154-156`).

The fourth, a line worker's observed defect, is direct observation and should be `observes`,
not `asserts` (`encodings/toyota__deepseek-v3.2.yaml:151-153`). That negative case matters:
`Party -> Signal` is not sufficient to infer assertion.

The fishery remains the strongest incentive case, but the graph fails to encode its author:
`reported_landings_effort` explicitly may omit illegal discards or misreported catch
(`encodings/ecosystem__gpt-5-codex.yaml:47-50`), and the encoder explicitly says the missing
reporting-party relation is the problem (`:270-277`). This is support for adding an edge, not
evidence that the current graph already tests it.

The broader prose claim is overstated. The hospital encoding explicitly excludes
`arrival_time_recording_practice` (`encodings/hospital__claude.yaml:308-312`), and no encoding
contains a founder pipeline or competitor-published-result node or edge. Those examples in
`uras.graph.md:96-101` were predictions, not corpus tests. Verdict: **recurrence is supported;
“throughout the existing corpus” and the named-example list are not.**

## Missing relations

These are missing because an existing edge is ill-typed or because an encoder explicitly
recorded the relationship only in prose. Counts are encodings needing the relation, not raw
edge counts.

| name | from-kind -> to-kind | evidence in the corpus | how many encodings need it |
|---|---|---|---:|
| `about` | `Estimate -> Estimand` | 27 edges in 10 encodings split between `estimates` (21) and `holds` (6); compare `encodings/factory__gpt-5-codex.yaml:241-249` with `encodings/spacex__deepseek-v3.2.yaml:141-146`. | 10 |
| `reads` | `Estimator -> Signal` | Eleven edges are forced through `measures` in four encodings (`encodings/ecosystem__deepseek-v3.2.yaml:110-115`); the thermostat has the same role reversed (`encodings/thermostat__claude.yaml:109-111`). | 5 |
| `governs` | `Policy -> Intervention` | Twenty edges across 13 encodings are arbitrarily split between `authorizes` (7) and `closes` (13); factory uses the former (`encodings/factory__deepseek-v3.2.yaml:184-192`), thermostat the latter (`encodings/thermostat__claude.yaml:136-138`). | 13 |
| `incurs` | `Intervention -> Delay` | Ten edges across seven encodings use `delays` backwards, e.g. `issue_po -> lead_time_delay` (`encodings/factory__deepseek-v3.2.yaml:202-204`). | 7 |
| `observes` | `Party -> Signal` | `line_worker -> observed_defect` is direct observation, not strategic reporting or `Signal -> Estimand` measurement (`encodings/toyota__deepseek-v3.2.yaml:151-153`). | 1 |
| `imposes` | `Party -> Constraint` | Two regulator edges use `authorizes`, e.g. `regulators -> safety_constraint` (`encodings/spacex__deepseek-v3.2.yaml:186-188`). | 2 |
| `preserves` | `Intervention -> Resource` | Postponing a plan preserves energy (`encodings/family__gpt-5-codex.yaml:270-272`); reducing hiring preserves cash (`encodings/portfolio_company__claude.yaml:150-152`). | 2 |
| `regulates` | `Intervention -> Resource` | Two fishery encodings force TAC-setting into opposite labels, `consumes` and `constrains` (`encodings/ecosystem__deepseek-v3.2.yaml:143-145`; `encodings/ecosystem__gpt-5-codex.yaml:219-224`). | 2 |
| `risks` | `Intervention -> Resource` | A tether test is encoded as consuming a vehicle despite its stated purpose of retaining it (`encodings/hop_aero__gpt5codex.yaml:251-265`). | 1 |
| `initiates` | `Party -> Revision` | `line_worker -> revise_standard_work` is currently `revises` (`encodings/toyota__gemini-2.5-pro.yaml:195-200`). | 1 |
| `calibrates` | `Calibration -> Estimator` | `demand_calibration` says it scores `demand_estimator`, but the edge is forced through `revises` (`encodings/venture_acme__claude.yaml:143-146,193-195`). | 1 |
| `enables` | `Intervention -> Signal` | `install_andon -> andon_pull` is forced through `revises`, although the intervention makes future evidence available (`encodings/toyota__claude.yaml:179-182,333-335`). | 1 |
| `couples` | `Intervention -> Intervention` | The factory encoder records in prose a contingent transfer of difficulty from stamped-housing quality to downstream assembly and says neither Constraint, Delay, nor Resource can carry it (`encodings/factory__gpt-5-codex.yaml:378-385`). | 1 |

Two prose demands should **not** automatically become relations:

- `SemanticArtifact` production/consumption/translation is a node-vocabulary failure first.
  The encoder says Signal and Estimate are the wrong endpoint kinds
  (`encodings/llm_agent_system__gpt-5-codex.yaml:361-369`). Adding verbs without representable
  artifact nodes would create more orphans.
- Payday and rest replenishment are real, but the family encoding has no payday/rest node to
  serve as an endpoint (`encodings/family__gpt-5-codex.yaml:327-333`). This supports
  `replenishes` semantically, but the concrete migration evidence comes from factory and
  hospital.

## Principled basis

**The current relation list is not closable.** It is an open English-verb list with no stated
typing rules. The evidence is not merely that new domains suggest new verbs. The existing
corpus already makes identical kind pairs choose different relations (`Policy -> Intervention`
uses both `authorizes` and `closes`; `Estimate -> Estimand` uses both `holds` and `estimates`)
and makes one relation cover opposite orientations (`Loop -> Intervention` and
`Intervention -> Loop`). A vocabulary cannot be “closed” when encoders cannot determine a
token from the endpoint roles.

A closable replacement can be derived from **typed slots on the primitives**, not from a list
of domain verbs:

| family | closed role slots |
|---|---|
| structural | `contains` for declared composition/membership |
| attribution | Party `holds` attitudes, `asserts` reports, `bears` consequences, and Party/System `authorizes` interventions |
| epistemic pipeline | Estimator `reads` Signal, `produces` Estimate; Estimate is `about` Estimand; Signal `measures` Estimand |
| normative/control | DesiredCondition `targets` Estimand; Policy `governs` Intervention; Constraint `constrains` its typed subject |
| calibration/change | Calibration `calibrates` Estimator; Revision/structural Intervention `revises` a schema-bearing target |
| temporal | Intervention `incurs` Delay; Delay `delays` its affected Signal or Intervention |
| resource effect | one typed resource-effect family with a required finite mode such as `decrease`, `increase`, `preserve`, `regulate`, or `risk`, rather than minting an unconstrained verb each time |

Loop roles should not be relations at all while `loops[]` already has the three named slots.
Keeping both representations guarantees the orientation drift seen in the corpus.

The closure rule should be mechanical:

1. Every relation has one semantic invariant and an explicit allowed `(from-kind, to-kind)`
   signature.
2. Endpoint kinds determine the role; two tokens may share a kind pair only when the
   distinction is independently observable (for example, resource increase versus decrease).
3. Shortcuts that skip a required intermediate primitive are invalid, not alternative
   encodings.
4. A new relation requires at least one concrete edge migration in the corpus. Prose-only
   predictions remain extension candidates.

With those rules, the relation algebra can be frozen **relative to the 19 primitives and their
declared slots**. The current 15 cannot be frozen. The thirteen missing roles above—and the
fact that several are one-off effects—show that merely appending more verbs will grow forever.
Freezing is defensible only after replacing the verb list with the typed-slot discipline and
a structured resource/effect relation.

## Harshest observation

The worst defect is not the three zero-use declarations. It is that the supposedly closed
vocabulary does not determine an edge label even when both endpoint kinds are known.
`Policy -> Intervention` is `authorizes` or `closes`; `Estimate -> Estimand` is `holds` or
`estimates`; estimator input is `measures` in one direction in four encodings and in the
opposite direction in the thermostat. Meanwhile `closes` duplicates fields already present in
`loops[]`.

That means successful validation currently proves only that an encoder selected **some
permitted word**, not that two encoders represented the same relationship the same way. The
relation vocabulary therefore defeats the determinacy purpose for which the canonical graph
was introduced (`uras.graph.md:77-82`). Declaring it closed before deriving typed roles would
freeze ambiguity, not an ontology.
