# Prospective pilot protocol — review draft

**Protocol status:** `DRAFT_PENDING_HUMAN_APPROVAL`
**Pilot status:** `NOT_STARTED`
**Repository baseline reviewed:** `872c60b2e959ea48d25524b74686e488f576ec6f`
**No real cases, outcomes, oracle, or scoring were accessed or created for this draft.**

This is a governance design, not qualification evidence. It does not authorize data collection, prediction generation, private scoring, branch/PR integration, capability promotion, or a release claim. Keep all real source records, case identifiers, predictions, outcomes, and any re-identifiable digests outside Git.

## Purpose and unit of analysis

Proposed purpose: evaluate whether one prospectively registered Metaphysics Lab prediction/claim workflow can be run with a fixed source, exact candidate, frozen claim universe, and outcome-blind lock. The pilot is not designed to establish general predictive superiority. Any later predictive-validity claim requires a separately approved analysis plan and adequate outcome maturity.

The unit of analysis, target population, prediction horizon, and primary estimand are **pending human decision**. No sample, event family, or scoring rule is selected by this draft.

## Required pre-run decisions

The human study owner must resolve and approve every item below before any real pilot input is accepted:

| Decision | Required record | Current status |
| --- | --- | --- |
| Study owner and data custodian | Named accountable owner and separate data custodian, if applicable | `PENDING` |
| Lawful source and consent | Exact source, permitted use, retention, access, withdrawal, and consent/basis | `PENDING` |
| Eligibility and census | Target population, inclusion/exclusion rules, census cutoff, duplicate handling, and unit of analysis | `PENDING` |
| Claim universe | Allowed claim families, granularity, direction, time horizon, and explicit out-of-scope claims | `PENDING` |
| Arms and comparator | Whether a paired baseline is appropriate; exact code/distribution SHAs and fixed configuration for every arm | `PENDING` |
| Time scope | Timezone, query/cutoff timestamp, window start/end, and endpoint convention | `PENDING` |
| Outcome definition | Evidence hierarchy, adjudication procedure, support/contradiction/indeterminate/out-of-universe labels | `PENDING` |
| Blinding | Which operators can see each arm and when the outcome adjudicator is unblinded | `PENDING` |
| Metrics | One primary metric and any secondary/descriptive metrics, with denominators and missingness rules | `PENDING` |
| Sample and stopping | Fixed target or fixed enrollment end, maturity delay, and no-peeking/stopping rules | `PENDING` |
| Withdrawal/deviation | Handling of withdrawals, late reports, protocol deviations, and unusable records | `PENDING` |
| Publication/privacy | What aggregate results may leave the private workspace and who reviews disclosure risk | `PENDING` |

If these choices cannot be specified before the lock, the pilot remains `NOT_STARTED`; do not substitute retrospective cases or choose thresholds after observing outcomes.

## Proposed execution sequence (requires approval)

1. **Approve and seal protocol.** Record the approved protocol version and SHA256, decision owners, source permissions, claim universe, time scope, arm identities, primary metric, sample/stopping rules, and privacy plan before processing any eligible case.
2. **Freeze source census privately.** A data custodian records the eligible-set manifest, exclusions and reasons, source provenance, and private digest in approved storage. Git receives no row-level or re-identifiable data.
3. **Bind exact candidate and configuration.** Record repository, exact candidate commit SHA, distribution/package SHA256, canonical manifest digest, capability/profile/rule versions, runtime/configuration, and the allowed input fields. No later code or configuration substitution is allowed within this pilot.
4. **Build one canonical authority chain.** For each case, bind the approved window policy and per-case claim authority to the source-record digest; bind the complete include census and sorted per-case authorities to one composite authority digest. The arm lock must reference that authority rather than create a second, competing claim universe.
5. **Generate and lock predictions before outcomes.** Use a fixed, approved input packet and predeclared arms. Store the canonical prediction bytes, candidate/configuration identity, claim IDs, timestamps, and digests in access-controlled storage. Record the lock receipt before the approved outcome window opens. An outcome-bearing source or oracle must be unavailable to prediction generation.
6. **Wait for the predeclared maturity point.** No scoring occurs while an outcome window is open or unresolved. Late, missing, contradictory, withdrawn, or unobservable outcomes follow the pre-registered label and missingness rules; they are not silently removed or relabeled.
7. **Adjudicate blind to arm.** An authorized reviewer applies only the pre-registered evidence hierarchy and labels. Preserve source citation, timestamp, adjudicator, and deviation record in private evidence storage. Unblind only after adjudication is sealed.
8. **Analyze the locked estimand.** Run only the approved metric implementation against the frozen denominator. Report uncertainty, indeterminate/missing counts, exclusions, deviations, and all predeclared controls. Do not infer event-level certainty from family coverage or an uncalibrated score.
9. **Review and publish only approved aggregates.** The study owner and privacy reviewer approve any aggregate disclosure. Keep raw material private. Any changed claim universe, candidate, horizon, metric, or stopping rule requires a new protocol version and a new prospective lock, not an amendment to this pilot after outcomes are visible.

## Lock and provenance record

The eventual private lock should bind, at minimum:

- approved protocol version and digest;
- source-census digest and inclusion/exclusion counts, with record-level material remaining private;
- exact repository commit, distribution/package digest, manifest digest, capability/profile/rule versions, runtime, and configuration;
- approved scope policy, timezone, query/cutoff, window endpoints, and endpoint convention;
- sorted opaque case IDs and per-case source/claim-authority digests;
- one composite claim-universe/authority digest;
- prediction/arm artifact digests, creation time, and lock receipt;
- identities/roles of the executor, custodian, and independent outcome adjudicator;
- predeclared primary metric, denominator, maturity, stopping, withdrawal, and deviation rules.

These records must be stored in an access-controlled location approved by the data owner. A hash of a predictable private record can itself leak information; do not place private hashes, IDs, timestamps, or small-cell counts in public Git without a disclosure review.

## Outcome and analysis safeguards

- Outcome labels and evidence rules must be defined before the first prediction lock. `indeterminate` is a valid result, not a negative or a removable row.
- An outcome window is not scored until its predeclared end and maturity delay have passed. No early stopping based on favorable results.
- The adjudicator must not see arm identity or prediction content until outcomes are sealed. The prediction executor must not have outcome/oracle access.
- The primary metric must match the model output. Do not report probability calibration unless the locked output actually contains probabilities and the approved metric is valid for them.
- Include all predeclared controls and adverse/contradictory outcomes. No post-hoc family mapping, threshold tuning, window expansion, candidate replacement, or selective case removal.
- A protocol deviation is recorded with time, reason, affected records, and whether the pre-registered analysis remains interpretable. A material deviation can make the pilot non-qualifying.
- One pilot result is local evidence for the specified scope only. It does not automatically qualify a capability, validate another profile, or authorize Experimental-to-Stable promotion.

## Research delta and architecture recommendation

Fresh read-only review found three distinct layers that should be reconciled before implementation:

1. Main at the pinned baseline already has prospective-validation code. Any pilot integration must first map its existing source, scope, and evidence contract; this draft does not create a parallel runtime or claim-authority registry.
2. PR #221 (`e28a51e9cb60961838300b8a0aea8e25696e9fb4`) proposes a deterministic composite authority over the S1 include census and per-case validated claim-authority manifests. Its PR description records a qualified engineering path but also `PRIVATE_S1_NOT_YET_LOCKED`, no oracle, no private scoring, and `promotion_allowed=false`.
3. `research/v1.6-prospective-arm-freeze-v1` (`dc95050640addf31e57ec637fdcf8e1483c42fb5`) adds an outcome-blind paired-arm sealing/orchestration path that binds a scope, claim authority, and downstream outputs. It remains research-branch code, not current main behavior.

### Concrete module and contract delta

The following responsibilities were checked against the exact baseline and branch heads; these files are not being imported or merged by this draft.

| Layer | Exact source and interface | What it binds | Current boundary |
| --- | --- | --- | --- |
| Main prospective validation | [`engine/distribution/prospective_validation.py` at `872c60b`](https://github.com/mvkaiii/metaphysics-lab/blob/872c60b2e959ea48d25524b74686e488f576ec6f/engine/distribution/prospective_validation.py): `classify_validation_context`, `build_validation_summary`; classifier `prospective-validation-v2-exp` | Forecast ID, lock/cutoff timestamps, question mode, knowledge-at-lock, prediction window, deterministic context class/digest, and clean-prospective denominator counts | It classifies/aggregates validation context. Its fixed input has no candidate/package SHA, source-census digest, per-case claim-authority manifest, or paired-arm output lock. Summary explicitly keeps superiority unestablished. |
| PR #221 composite authority | [`engine/distribution/prospective_claim_authority_set.py` at `e28a51e`](https://github.com/mvkaiii/metaphysics-lab/blob/e28a51e9cb60961838300b8a0aea8e25696e9fb4/engine/distribution/prospective_claim_authority_set.py): `build_claim_authority_set`, `validate_claim_authority_set`; schema `v1.6-prospective-claim-authority-set.v1` | Validated S1 sampling/source manifest, exact deterministic INCLUDE census, opaque case IDs, each source-record digest, per-case claim-authority profile/digest, and one canonical composite authority digest | This makes the claim universe auditable, but it does not seal paired arm outputs or adjudicate outcomes. The PR description reports `PRIVATE_S1_NOT_YET_LOCKED`; no private scoring or promotion is authorized. |
| Arm-freeze research branch | [`engine/distribution/prospective_arm_freeze.py` at `dc95050`](https://github.com/mvkaiii/metaphysics-lab/blob/dc95050640addf31e57ec637fdcf8e1483c42fb5/engine/distribution/prospective_arm_freeze.py): `build_prospective_arm_freeze`; schema `v1.6-prospective-arm-freeze.v1` | Frozen timezone/window and pre-outcome timestamp, authority/scope digests, locked claim IDs, forecast/ranking/interpretation digests, and paired Legacy/Candidate output bundles | It is a substantial orchestration path that rebuilds and validates downstream claim chains. Its output is `WAITING_FOR_OUTCOME`, `oracle_status=NOT_CREATED`, `scoring_status=NOT_PERFORMED`, and `retuning_status=PROHIBITED`; it does not establish outcome validity. |

The convergence boundary is therefore: use main's prospective validator for context classification and denominator semantics; use one validated source census plus per-case authority as the sole claim-universe authority; let any future arm-freeze receipt reference that same composite digest and exact candidate/configuration; then send only post-window, adjudicated outcomes into the existing validation summary path. Do not maintain a second claim universe, candidate score, or competing meaning of “clean prospective.” Before implementation, a focused design review must map how the composite authority digest and arm-lock receipt become provenance for main's `forecast_id`/validation record without changing its existing classifier semantics.

**Proposed design delta, pending review:** use one chain of authority—approved source census → per-case authority → one composite authority digest → arm/output lock → post-window blind adjudication. The composite authority owns the claim universe; the arm-freeze receipt references it and must not redefine claims or scoring. Reconcile this chain with main's existing `engine/distribution/prospective_validation.py` before selecting modules or writing integration code. Do not merge either research branch wholesale.

PR #219 (`3d6bba9efa37b105aee198215f90f00e3ed99229`) remains retrospective yearly-Ziwei research. Its PR description says prospective validation was not executed and promotion is not allowed. It is not a candidate for this pilot unless a separately approved claim-universe review shows a direct dependency.

The cited PR descriptions are source-reported status, not a fresh hosted qualification or independent verification of every linked run. No PR/branch was retargeted, merged, closed, or deleted during this review.

## Readiness gate and current disposition

Do not start a real pilot until all of the following are recorded and approved:

- every pre-run decision above is resolved and the protocol is versioned/sealed;
- lawful data access, consent, withdrawal, privacy, and retention are confirmed by the responsible human owner;
- the exact candidate, package, runtime, source manifest, claims, arms, horizon, and metric are frozen;
- tests demonstrate that source/claim/candidate/window changes invalidate the lock, that outcome/oracle data cannot enter blind prediction generation, and that duplicate, immature, withdrawn, or indeterminate outcomes cannot be silently scored;
- the independent adjudication and secure storage path are available.

**Current decision:** `NOT_STARTED`. No participant/case was enrolled, no prediction was locked, no outcome was inspected, no pilot metric was computed, and no qualification or promotion evidence was created.

**Human review requested:** approve, amend, or reject the decision table and the proposed single-authority chain before any real-data implementation or pilot run.
