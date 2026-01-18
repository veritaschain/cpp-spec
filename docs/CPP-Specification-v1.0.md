# Capture Provenance Profile (CPP) Specification

**Version:** 1.0  
**Status:** Release Candidate  
**Date:** 2026-01-18  
**Document ID:** VSO-CPP-SPEC-001  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** CC BY 4.0 International

---

## Abstract

The Capture Provenance Profile (CPP) is an open specification for cryptographically verifiable media capture provenance. Unlike edit-history approaches such as C2PA, CPP focuses on proving "this media was actually captured at this moment" with **deletion detection**, **external timestamping**, and **privacy-by-design** architecture.

CPP addresses the fundamental limitations of self-attestation models by requiring independent third-party verification (RFC 3161 TSA) and implementing mathematically provable **Completeness Invariants** that detect any missing events.

---

## 1. Introduction

### 1.1 Problem Statement

Existing solutions including C2PA face critical challenges:

| Challenge | Description | CPP Solution |
|-----------|-------------|--------------|
| **Self-Attestation** | Creators sign own claims | RFC 3161 TSA mandatory |
| **Metadata Stripping** | 95%+ stripped by platforms | Verification URL + PHASH |
| **No Deletion Detection** | Missing events undetected | Completeness Invariant |
| **"Verified ≠ Truth"** | UI misleads users | "Provenance Available" terminology |
| **Trust List Gatekeeping** | Vendor-controlled | Open TSA ecosystem |
| **Exclusion List Abuse** | Some changes bypass signature | NO exclusion lists |
| **Privacy Risks** | Identity disclosure required | Privacy-first design |

### 1.2 Core Innovations

1. **External Third-Party Verification** (RFC 3161 TSA mandatory)
2. **Completeness Invariant** (XOR hash sum for deletion detection)
3. **Verification URL Architecture** (survives metadata stripping)
4. **Privacy by Design** (location OFF default, zero-knowledge ACE)
5. **Clear UI Guidelines** ("Provenance Available" not "Verified")
6. **No Exclusion Lists** (all changes invalidate signature)
7. **C2PA Interoperability** (complement, not compete)

---

## 2. Design Philosophy

### 2.1 "Verify, Don't Trust"

CPP rejects self-attestation:

```
C2PA Model: Creator signs → "Trust me" → NO INDEPENDENT CHECK
CPP Model:  Creator signs → TSA countersigns → INDEPENDENT THIRD-PARTY
```

### 2.2 "Absence of Evidence is Evidence"

Completeness Invariant detects missing events:

```
Stored hash_sum:   H(E1) ⊕ H(E2) ⊕ H(E3) ⊕ H(E4)
Computed (E3 missing): H(E1) ⊕ H(E2) ⊕ H(E4)
Result: Mismatch → VIOLATION DETECTED
```

### 2.3 "Provenance ≠ Truth"

CPP proves: ✅ Capture timing, ✅ Device identity, ✅ No deletions
CPP does NOT prove: ❌ Content truth, ❌ Scene authenticity, ❌ Source trustworthiness

---

## 3. Architecture

### 3.1 Three-Layer Architecture

```
┌────────────────────────────────────────────────────────┐
│ Layer 3: External Verifiability (RFC 3161 TSA)        │
│   → Independent third-party timestamp                  │
├────────────────────────────────────────────────────────┤
│ Layer 2: Collection Integrity (Merkle + CI)           │
│   → Deletion detection via XOR hash sum                │
├────────────────────────────────────────────────────────┤
│ Layer 1: Event Integrity (SHA-256 + Ed25519)          │
│   → Individual event tamper-evidence                   │
└────────────────────────────────────────────────────────┘
```

### 3.2 Verification URL

```
https://verify.veritaschain.org/cpp/{verification_code}
SLA: 99.95% availability, 50+ year retention
```

---

## 4. Event Types

| Type | Code | Description | Required |
|------|------|-------------|----------|
| CAPTURE | `CPP_CAPTURE` | Media from sensor | Yes |
| SEAL | `CPP_SEAL` | Collection finalized | Yes |
| SHARE | `CPP_SHARE` | Shared with link | No |
| DELETE | `CPP_DELETE` | Crypto-shredding | No |
| CAPTURE_ATT | `CPP_CAPTURE_ATT` | With biometric (ACE) | ACE only |

---

## 5. Data Model

### 5.1 CAPTURE Event

```json
{
  "cpp_version": "1.0",
  "event_id": "01932f5a-7b8c-7def-8abc-123456789012",
  "event_type": "CPP_CAPTURE",
  "timestamp": "2026-01-18T10:30:00.000Z",
  "device_id": "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
  "sequence_number": 1,
  "prev_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "payload": {
    "media_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "media_type": "image/heic",
    "capture_device": {
      "manufacturer": "Apple",
      "model": "iPhone 16 Pro"
    },
    "location": null,
    "collection_id": "album:vacation-2026"
  },
  "signature": {
    "algorithm": "Ed25519",
    "public_key": "base64:...",
    "value": "base64:..."
  }
}
```

### 5.2 SEAL Event

```json
{
  "cpp_version": "1.0",
  "event_type": "CPP_SEAL",
  "payload": {
    "collection_id": "album:vacation-2026",
    "event_count": 47,
    "merkle_root": "sha256:...",
    "completeness_invariant": {
      "expected_count": 47,
      "hash_sum": "sha256:xor-of-all-hashes...",
      "first_timestamp": "2026-01-18T08:00:00.000Z",
      "last_timestamp": "2026-01-18T17:55:00.000Z"
    },
    "external_anchor": {
      "type": "RFC3161",
      "tsa_url": "https://freetsa.org/tsr",
      "timestamp_token": "base64:..."
    }
  }
}
```

### 5.3 Verification Pack

```json
{
  "verification_pack_version": "1.0",
  "verification_code": "CPP-2026-ABC123XYZ",
  "verification_url": "https://verify.veritaschain.org/cpp/CPP-2026-ABC123XYZ",
  "capture_event": { },
  "seal_event": { },
  "merkle_proof": {
    "leaf_hash": "sha256:...",
    "audit_path": ["sha256:...", "sha256:..."],
    "directions": ["L", "R"]
  },
  "completeness_invariant": { },
  "external_anchor": { },
  "recovery": {
    "phash_algorithm": "pHash-DCT",
    "phash_value": "d4c3b2a1..."
  }
}
```

---

## 6. Cryptographic Requirements

| Purpose | Algorithm | Requirement |
|---------|-----------|-------------|
| Event hash | SHA-256 | REQUIRED |
| Signature | Ed25519 | REQUIRED |
| Merkle tree | SHA-256 (RFC 6962) | REQUIRED |
| Completeness | XOR of SHA-256 | REQUIRED |
| Perceptual hash | pHash-DCT | RECOMMENDED |
| Post-quantum | ML-DSA-65 | RESERVED |

**CRITICAL: NO EXCLUSION LISTS** - All fields covered by signature.

---

## 7. Completeness Invariant

### 7.1 Definition

```
CI = {
  expected_count: n,
  hash_sum: H(E₁) ⊕ H(E₂) ⊕ ... ⊕ H(Eₙ),
  first_timestamp: T₁,
  last_timestamp: Tₙ
}
```

### 7.2 Verification

```python
def verify_completeness(events, seal):
    ci = seal.completeness_invariant
    if len(events) != ci.expected_count:
        return VIOLATION
    computed = bytes(32)
    for e in events:
        computed = xor(computed, sha256(e))
    if computed != ci.hash_sum:
        return VIOLATION
    return VALID
```

### 7.3 Security

| Attack | Detection |
|--------|-----------|
| Delete event | Hash sum mismatch |
| Add fake event | Count + hash mismatch |
| Reorder | Chain hash mismatch |

---

## 8. ACE (Attested Capture Extension)

> "We prove authentication was attempted. We store ZERO biometric data."

| ✅ RECORDS | ❌ DOES NOT RECORD |
|------------|-------------------|
| Auth method | Facial geometry |
| Result | Fingerprint data |
| Duration | Biometric templates |
| Device attestation | Raw sensor data |

---

## 9. Conformance Levels

| Level | TSA | ACE | Completeness |
|-------|-----|-----|--------------|
| Bronze | Optional | Optional | REQUIRED |
| Silver | Daily | Optional | REQUIRED |
| Gold | Per-capture | REQUIRED | REQUIRED |

---

## 10. Privacy

- **Location**: OFF by default
- **Identity**: Anonymous/Pseudonymous/Identified modes
- **Crypto-shredding**: GDPR-compliant deletion

---

## 11. UI Guidelines

| ✅ USE | ❌ AVOID |
|--------|---------|
| "Provenance Available" | "Verified" |
| "Capture Recorded" | "Authenticated" |
| Information icon (ℹ️) | Checkmark (✓) |

**Required disclosure:**
> "This shows capture data. It does NOT verify content truthfulness."

---

## 12. C2PA Interoperability

CPP complements C2PA:

| C2PA | CPP |
|------|-----|
| "How was this edited?" | "Was this captured?" |
| No deletion detection | Completeness Invariant |
| Optional external anchor | Required (Silver+) |

Export format:
```json
{"c2pa.actions": [{"action": "c2pa.captured",
  "parameters": {"vso.cpp.verification_url": "..."}}]}
```

---

## 13. References

- RFC 2119, RFC 3161, RFC 6962, RFC 8032, RFC 8785
- C2PA: https://c2pa.org/specifications/
- VCP: https://github.com/veritaschain/vcp-spec

---

**Copyright © 2026 VeritasChain Standards Organization. CC BY 4.0**
