# Capture Provenance Profile (CPP)

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Spec Version](https://img.shields.io/badge/spec-v1.4%20Released-blue.svg)](docs/CPP-Specification-v1.4.md)
[![Part of VAP](https://img.shields.io/badge/VAP-Framework-green.svg)](https://github.com/veritaschain/vap-spec)

**Open specification for cryptographically verifiable media capture provenance.**

CPP records "this media was captured at this moment by this device" with hash-chain deletion detection, external timestamping, and privacy-by-design. It is a domain profile of the [VAP (Verifiable AI Provenance Framework)](https://github.com/veritaschain/vap-spec) metaframework. "Capture" is CPP's domain term; "Content" belongs to CAP (Content / Creative AI Profile).

### Status

| Version | Status | Date | File |
|---------|--------|------|------|
| **v1.4** | **Released** (tag `1.4`) — current | 2026-01-29 | [`docs/CPP-Specification-v1.4.md`](docs/CPP-Specification-v1.4.md) |
| v1.5 | Not released — Pre-Publish Verification Extension. Its header reads "Final", but no tagged release exists, so it is not a Released version under the VAP v1.2 §4.5.2 status vocabulary | 2026-01-30 | [`docs/CPP-Specification-v1.5.md`](docs/CPP-Specification-v1.5.md) |
| v1.0 – v1.3 | Superseded | 2026-01 | [`docs/`](docs/) |

A VAP v1.2 conformance mapping for CPP v1.4 is due and not yet published. Until it is, CPP may not be described as VAP v1.2 conformant (VAP v1.2 §10.4).

### Implementation status (mandatory disclosure)

As of September 2026: **zero external implementations** of CPP or any other VAP profile, and **zero Evidence Packs accepted in any proceeding**. VeritasChain Co., Ltd., which provides the operating base of VSO, holds ten paid service contracts with European organizations in regulatory technology, financial trading, and audit and assurance (client names withheld pending individual consent); those contracts are not external implementations and are not independent validation of CPP. Where a VeritasChain product implements CPP, it is a first-party implementation: VSO and VeritasChain Co., Ltd. share a founder.

---

## 🎯 Why CPP?

Existing content provenance solutions face critical challenges:

| Problem | CPP Mechanism |
|---------|--------------|
| **Self-attestation abuse** | RFC 3161 TSA countersignature (independent third party) from CPP-TIMESTAMPED upward |
| **Metadata stripped by platforms** | Verification URL + PHASH recovery |
| **Deletion from a capture history goes unnoticed** | PrevHash event chain (CPP v1.1 §9); legitimate deletions recorded as TOMBSTONE events |
| **"Verified" misleads users** | "Provenance Available" terminology |
| **Trust list gatekeeping** | Open TSA ecosystem (free options) |
| **Exclusion list vulnerabilities** | NO exclusion lists |

## 🔑 Key Features

### 1. Deletion Detection (hash chain)
Each event carries the hash of the previous one (CPP v1.1 §9), so removing an event from the middle of the chain is detectable:
```
Stored:   E1 → E2 → E3 → E4
Deleted:  E1 → E2 → [E3 missing] → E4
Verify:   E4.PrevHash ≠ EventHash(E2) → violation detected
```
Legitimate deletions are recorded as TOMBSTONE events (crypto-shredding), not removed from the chain.

**Scope.** Events removed after inclusion in a TSA-anchored Merkle batch are detectable against that anchor (CPP v1.2–v1.3). The most recent events, if removed before they are anchored, may leave no trace (recorded but lost before anchoring). An event that was never recorded leaves nothing to detect (pre-measurement drop) — a structural limit that no later version will close.

The XOR-sum "Completeness Invariant" and the SEAL event of CPP v1.0 were removed in v1.1 (replaced by batch anchoring); `tools/completeness_invariant.py` and `test-vectors/completeness/` are v1.0 artifacts.

### 2. External Third-Party Timestamping
RFC 3161 TSA timestamps remove sole reliance on the creator's own clock and signature:
```
Creator signs → TSA countersigns → independently checkable timestamp
```

### 3. Privacy by Design
- Location: OFF by default
- Biometric attestation without storing biometric data (ACE)
- Crypto-shredding — may support GDPR Art. 17 erasure obligations; does not itself determine compliance

### 4. C2PA Interoperability
Complement, not compete:
- C2PA: "How was this edited?"
- CPP: "Is there a verifiable capture record for this media — when, and by which device?" (CPP does not establish scene authenticity or content truthfulness)

---

## 📁 Repository Structure

```
cpp-spec/
├── docs/
│   └── CPP-Specification-v1.0.md    # Superseded
│   └── CPP-Specification-v1.1.md    # Superseded
│   └── CPP-Specification-v1.2.md    # Superseded
│   └── CPP-Specification-v1.3.md    # Superseded
│   └── CPP-Specification-v1.4.md    # Main specification (Released, tag 1.4)
│   └── CPP-Specification-v1.5.md    # Proposed extension (not released)
├── schemas/                          # JSON schemas (CPP v1.0 format)
│   ├── cpp/                          # Core JSON schemas
│   └── ace/                          # ACE extension schemas
├── examples/                         # Examples (CPP v1.0 format)
│   ├── cpp-core/                     # Core examples
│   └── cpp-ace/                      # ACE examples
├── test-vectors/                     # Test data (CPP v1.0; JCS tests remain applicable)
├── regulatory-mapping/               # Regulatory relevance mapping (v1.0; under revision)
└── tools/                            # Reference utilities (CPP v1.0)
```

---

## 🚀 Quick Start

> The schemas and the example below use the **CPP v1.0** event format. From v1.1, `CPP_CAPTURE` became `INGEST`, `CPP_SEAL` was removed, and ES256 is used for mobile platforms (CPP v1.1 Appendix A). Updated v1.4 schemas and examples have not yet been published.

### Verification URL
The verification URL form differs by version (v1.0: `https://verify.veritaschain.org/cpp/{verification_code}`; v1.1: `/p/{proof_id}`; v1.5 proposal: `/v/{proof_id}`). CPP v1.4 does not define one.

### Basic Event Structure (CPP v1.0 format)
```json
{
  "cpp_version": "1.0",
  "event_type": "CPP_CAPTURE",
  "timestamp": "2026-01-18T10:30:00.000Z",
  "payload": {
    "media_hash": "sha256:...",
    "media_type": "image/heic",
    "collection_id": "album:vacation-2026"
  },
  "signature": {
    "algorithm": "Ed25519",
    "value": "base64:..."
  }
}
```

---

## 📊 Conformance Levels (CPP v1.4 §8)

| Level | Core | TSA | Merkle | Depth | Attestation |
|-------|------|-----|--------|-------|-------------|
| CPP-BASIC | ✓ | - | - | - | - |
| CPP-TIMESTAMPED | ✓ | ✓ | - | - | - |
| CPP-STANDARD | ✓ | ✓ | ✓ | - | - |
| CPP-ENHANCED | ✓ | ✓ | ✓ | ✓ | - |
| CPP-FULL | ✓ | ✓ | ✓ | ✓ | ✓ |

The Bronze / Silver / Gold levels of CPP v1.0–v1.1 are superseded.

> **Known divergences from VAP v1.2** (non-exhaustive; to be resolved in the CPP VAP v1.2 conformance mapping):
> - **Anchoring.** VAP v1.2 requires external anchoring at every conformance level (INT-006; "there is no anchorless conformance level", §8.1). CPP-BASIC has no external timestamp or anchor, so it cannot support a VAP v1.2 conformance claim.
> - **Merkle domain separation.** VAP v1.2 §4.1.4 requires RFC 6962 leaf/node prefixes (0x00 / 0x01). CPP v1.3/v1.4 compute `LeafHash = SHA256(EventHash)` and `SHA256(Left || Right)` without prefixes and pad by duplicating the last leaf (CPP v1.4 Appendix C).
> - **Merkle batching.** INT-006 requires Merkle batching and external anchoring of signed roots at every level; CPP-TIMESTAMPED has no Merkle batching.
> - **Completeness binding.** INT-008 requires each anchor record to bind event count, first/last event identifiers, and a policy identifier; the CPP anchor data model (v1.3 §4) binds the tree size only.

---

## 🔗 Related Projects

- [VAP Framework](https://github.com/veritaschain/vap-spec) - Parent metaframework (v1.2, Draft 3)
- [VCP (VeritasChain Protocol)](https://github.com/veritaschain/vcp-spec) - Algorithmic trading
- [CAP (Content / Creative AI Profile)](https://github.com/veritaschain/cap-spec) - AI content generation and IP workflows

## 🌐 Standardization

| Body | Document | Status |
|------|----------|--------|
| IETF | [`draft-vso-cpp-core-03`](https://datatracker.ietf.org/doc/draft-vso-cpp-core/) | Individual Internet-Draft, active. Not adopted by any IETF Working Group; no standing in the IETF standards process. Its title still reads "Content Provenance Profile" and is to be corrected to "Capture Provenance Profile" at the next revision |

---

## 📜 UI Guidelines

**CPP explicitly avoids "Verified" terminology:**

| ✅ Use | ❌ Avoid |
|--------|---------|
| "Provenance Available" | "Verified" |
| "Capture Recorded" | "Authenticated" |
| ℹ️ Information icon | ✓ Checkmark |

> **Required disclosure (CPP v1.1 §12):** "This shows capture provenance. It does NOT verify content truthfulness or signer identity."

---

## ⚖️ Legal Scope (VAP v1.2 §1.6, adopted verbatim)

> VAP and its domain profiles define mechanisms for producing **cryptographically verifiable evidence** of AI system decisions. Conformance to VAP or any profile: (a) does **not** constitute compliance with the EU AI Act, GDPR, MiFID II/III, CAT Rule 613, NIS2, FDA SaMD guidance, or any other law or regulation; (b) does **not** constitute a legal determination that any technical mechanism (including crypto-shredding) satisfies a specific legal obligation; (c) does **not** warrant the correctness, fairness, or safety of the underlying AI decisions — only the integrity, completeness (at anchor granularity), and attributability of their records. VAP generates evidence; competent authorities and courts evaluate it.

Whether any CPP record is admissible or sufficient in a proceeding is for the court or authority in that matter to decide.

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

- Specification: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Code examples: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)

---

## 📞 Contact

- **Standards:** standards@veritaschain.org
- **Technical:** technical@veritaschain.org
- **Website:** https://veritaschain.org

---

**Copyright © 2026 VeritasChain Standards Organization**
