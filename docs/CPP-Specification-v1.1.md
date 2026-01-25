# Capture Provenance Profile (CPP) Specification

**Version:** 1.1  
**Status:** Release Candidate  
**Date:** 2026-01-25  
**Document ID:** VSO-CPP-SPEC-002  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** CC BY 4.0 International

---

## Abstract

The Capture Provenance Profile (CPP) is an open specification for cryptographically verifiable media capture provenance. Unlike edit-history approaches such as C2PA, CPP focuses on proving "this media was actually captured at this moment" with **deletion detection**, **external timestamping**, and **privacy-by-design** architecture.

CPP v1.1 updates the cryptographic requirements to support hardware-backed key storage on mobile devices (iOS Secure Enclave, Android StrongBox) and adds **Signer Information** for self-attested identity with clear verification semantics.

---

## 1. Changes from v1.0

| Item | v1.0 | v1.1 | Rationale |
|------|------|------|-----------|
| **Signature Algorithm** | Ed25519 REQUIRED | ES256 REQUIRED, Ed25519 OPTIONAL | iOS Secure Enclave native support |
| **Event Types** | CPP_CAPTURE, CPP_SEAL | INGEST, EXPORT | Simplified terminology |
| **SignerInfo** | Not defined | OPTIONAL | Self-attested identity support |
| **TSA Response** | timestamp_token | TSAResponse (base64 DER) | Explicit RFC3161 token storage |
| **Event Structure** | Flat with payload | Structured with Asset, CaptureContext | Better organization |

---

## 2. Design Philosophy

### 2.1 "Verify, Don't Trust"

CPP rejects self-attestation for **timestamps**:

```
Self-Attestation: Creator claims time → "Trust me" → NO INDEPENDENT CHECK
CPP Model:       Creator signs → TSA countersigns → INDEPENDENT THIRD-PARTY
```

### 2.2 SignerInfo: "Self-Attested, Not Self-Verified"

CPP allows **self-attested identity** (SignerInfo) with explicit semantics:

| What CPP Proves | What CPP Does NOT Prove |
|-----------------|------------------------|
| ✅ Someone claimed this name at capture time | ❌ The name is real/legal |
| ✅ The claim is tamper-evident (signed) | ❌ Identity verification occurred |
| ✅ The claim existed before TSA timestamp | ❌ The person is who they claim |

**UI Requirement:** Display as "Self-Attested Name" not "Verified Identity"

### 2.3 "Provenance ≠ Truth"

CPP proves: ✅ Capture timing, ✅ Device identity, ✅ No deletions, ✅ Name claim exists  
CPP does NOT prove: ❌ Content truth, ❌ Scene authenticity, ❌ Identity verification

---

## 3. Architecture

### 3.1 Three-Layer Architecture

```
┌────────────────────────────────────────────────────────────┐
│ Layer 3: External Verifiability (RFC 3161 TSA)             │
│   → Independent third-party timestamp                       │
│   → TSAResponse contains signed TimeStampToken              │
├────────────────────────────────────────────────────────────┤
│ Layer 2: Collection Integrity (Merkle + Chain)             │
│   → Deletion detection via hash chain (PrevHash)           │
│   → Merkle root for batch anchoring                        │
├────────────────────────────────────────────────────────────┤
│ Layer 1: Event Integrity (SHA-256 + ES256/ECDSA)           │
│   → Individual event tamper-evidence                        │
│   → Hardware-backed key (Secure Enclave)                   │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Verification URL

```
https://verify.veritaschain.org/p/{proof_id}
SLA: 99.95% availability, 50+ year retention
```

---

## 4. Event Types

| Type | Code | Description | Required |
|------|------|-------------|----------|
| INGEST | `INGEST` | Media captured from sensor | Yes |
| EXPORT | `EXPORT` | Proof shared externally | No |
| TOMBSTONE | `TOMBSTONE` | Crypto-shredding (deletion) | No |

---

## 5. Data Model

### 5.1 INGEST Event (Capture)

```json
{
  "EventID": "01932f5a-7b8c-7def-8abc-123456789012",
  "ChainID": "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
  "PrevHash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "Timestamp": "2026-01-25T10:30:00.000Z",
  "EventType": "INGEST",
  "HashAlgo": "SHA256",
  "SignAlgo": "ES256",
  "Asset": {
    "AssetID": "asset-uuid-here",
    "AssetType": "IMAGE",
    "AssetHash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "AssetName": "IMG_0001.HEIC",
    "AssetSize": 2048576,
    "MimeType": "image/heic"
  },
  "CaptureContext": {
    "DeviceID": "urn:uuid:device-uuid-here",
    "DeviceModel": "iPhone 16 Pro",
    "OSVersion": "iOS 18.2",
    "AppVersion": "1.0.0",
    "KeyAttestation": {
      "AttestationType": "SECURE_ENCLAVE",
      "AttestationData": "base64:...",
      "KeyID": "key-uuid-here"
    },
    "HumanAttestation": null
  },
  "SignerInfo": {
    "Name": "John Doe",
    "Identifier": null,
    "AttestedAt": "2026-01-25T10:29:55.000Z"
  },
  "SensorData": null,
  "CameraSettings": {
    "FlashMode": "off",
    "CameraPosition": "back"
  },
  "EventHash": "sha256:...",
  "Signature": "base64:..."
}
```

### 5.2 SignerInfo (Self-Attested Identity)

```json
{
  "SignerInfo": {
    "Name": "John Doe",
    "Identifier": "employee-id-12345",
    "AttestedAt": "2026-01-25T10:29:55.000Z"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | string | REQUIRED | Self-attested name |
| Identifier | string | OPTIONAL | External identifier (employee ID, etc.) |
| AttestedAt | ISO8601 | REQUIRED | When the attestation was made |

**Verification Semantics:**

1. SignerInfo is **included in EventHash calculation** → tamper-evident
2. EventHash is **included in TSA anchor** → timestamp-bound
3. Third-party verifier can confirm: "This name claim existed before TSA timestamp"
4. Third-party verifier **CANNOT** confirm: "This person is actually John Doe"

### 5.3 HumanAttestation (Biometric Verification)

When biometric authentication is used at capture time:

```json
{
  "HumanAttestation": {
    "Verified": true,
    "Method": "FaceID",
    "VerifiedAt": "2026-01-25T10:29:58.000Z",
    "CaptureOffsetMs": 150,
    "SessionNonce": "random-nonce-here"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| Verified | boolean | Authentication result |
| Method | string | FaceID, TouchID, OpticID, Passcode, None |
| VerifiedAt | ISO8601 | Authentication timestamp |
| CaptureOffsetMs | integer | Time between auth and capture (ms) |
| SessionNonce | string | Binding nonce for auth-capture link |

**Privacy:** Zero biometric data stored. Only the fact that authentication was attempted/succeeded.

### 5.4 Anchor (RFC 3161 TSA)

```json
{
  "Anchor": {
    "AnchorID": "anchor-uuid-here",
    "AnchorType": "RFC3161",
    "MerkleRoot": "sha256:...",
    "MerkleProof": ["sha256:...", "sha256:..."],
    "MerkleIndex": 0,
    "TSAResponse": "base64:MIAGCSqGSIb3DQEHAqCAMIACAQEx...",
    "TSATimestamp": "2026-01-25T10:31:00.000Z",
    "TSAService": "https://rfc3161.ai.moda"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| AnchorID | string | REQUIRED | Unique anchor identifier |
| AnchorType | string | REQUIRED | Always "RFC3161" |
| MerkleRoot | string | REQUIRED | Root hash anchored to TSA |
| MerkleProof | array | REQUIRED | Audit path for event |
| MerkleIndex | integer | REQUIRED | Leaf position in tree |
| **TSAResponse** | string | **REQUIRED** | **RFC3161 TimeStampToken (DER/base64)** |
| TSATimestamp | ISO8601 | REQUIRED | Parsed genTime from TST |
| TSAService | string | REQUIRED | TSA endpoint URL |

**CRITICAL:** TSAResponse MUST contain the complete RFC 3161 TimeStampToken for independent verification.

### 5.5 Verification Pack (Export)

```json
{
  "proof_version": "1.1",
  "proof_type": "CPP_INGEST_PROOF",
  "proof_id": "01932f5a-7b8c-7def-8abc-123456789012",
  "event": {
    "event_id": "...",
    "event_type": "INGEST",
    "timestamp": "2026-01-25T10:30:00.000Z",
    "asset_hash": "sha256:...",
    "asset_type": "IMAGE",
    "asset_name": "IMG_0001.HEIC"
  },
  "event_hash": "sha256:...",
  "signature": {
    "algo": "ES256",
    "value": "base64:..."
  },
  "public_key": "base64:...",
  "timestamp_proof": {
    "type": "RFC3161",
    "issued_at": "2026-01-25T10:31:00.000Z",
    "token": "base64:MIAGCSqGSIb3DQEHAqCAMIACAQEx...",
    "merkle_root": "sha256:...",
    "tsa_service": "https://rfc3161.ai.moda"
  },
  "attested": true,
  "signer_info": {
    "name": "John Doe",
    "identifier": null,
    "attested_at": "2026-01-25T10:29:55.000Z"
  }
}
```

---

## 6. Cryptographic Requirements

| Purpose | Algorithm | Requirement | Notes |
|---------|-----------|-------------|-------|
| Event hash | SHA-256 | REQUIRED | All hashes prefixed with `sha256:` |
| Signature | ES256 (ECDSA P-256) | REQUIRED | Secure Enclave compatible |
| Signature | Ed25519 | OPTIONAL | For non-mobile implementations |
| Merkle tree | SHA-256 (RFC 6962) | REQUIRED | Binary tree structure |
| Hash chain | SHA-256 | REQUIRED | PrevHash links events |
| Post-quantum | ML-DSA-65 | RESERVED | Future consideration |

**CRITICAL: NO EXCLUSION LISTS** - All fields covered by signature, including SignerInfo.

### 6.1 EventHash Calculation

EventHash is calculated over the **canonicalized JSON** (RFC 8785 JCS) of the event **excluding** EventHash and Signature fields:

```python
def calculate_event_hash(event):
    # Remove fields that depend on the hash
    event_copy = copy(event)
    del event_copy["EventHash"]
    del event_copy["Signature"]
    
    # Canonicalize (RFC 8785 JCS)
    canonical = jcs_canonicalize(event_copy)
    
    # Hash
    return "sha256:" + sha256(canonical).hex()
```

### 6.2 Signature Verification

```python
def verify_signature(event, public_key):
    # Recalculate EventHash
    computed_hash = calculate_event_hash(event)
    
    # Verify EventHash matches
    if computed_hash != event["EventHash"]:
        return INVALID
    
    # Verify signature over EventHash bytes
    hash_bytes = bytes.fromhex(event["EventHash"].replace("sha256:", ""))
    signature_bytes = base64_decode(event["Signature"])
    
    return ecdsa_verify(public_key, hash_bytes, signature_bytes)
```

---

## 7. SignerInfo Verification Semantics

### 7.1 What Verification Proves

When a third party verifies a CPP proof with SignerInfo:

| Verification Step | What It Proves |
|------------------|----------------|
| 1. EventHash matches recalculated | SignerInfo was not modified after signing |
| 2. Signature valid | Device with this key signed this data |
| 3. TSA timestamp valid | This data existed before TSA genTime |
| 4. TSAResponse verifiable | Independent TSA confirms timestamp |

**Combined proof:** "At the time of TSA timestamp, a device claimed this capture was made by '{Name}'"

### 7.2 What Verification Does NOT Prove

| Claim | Status |
|-------|--------|
| The person is actually named "{Name}" | ❌ NOT PROVEN |
| The person had legal ID verification | ❌ NOT PROVEN |
| The name matches device owner | ❌ NOT PROVEN |
| The person was physically present | ❌ NOT PROVEN (unless HumanAttestation present) |

### 7.3 UI Guidelines for SignerInfo

| ✅ CORRECT Display | ❌ INCORRECT Display |
|-------------------|---------------------|
| "Self-Attested: John Doe" | "Verified by: John Doe" |
| "Claimed signer: John Doe" | "Authenticated: John Doe" |
| "Name on record: John Doe" | "Identity confirmed: John Doe" |

**Required disclosure when SignerInfo present:**
> "This name is self-attested by the device operator. It has NOT been independently verified."

---

## 8. TSA Verification (RFC 3161)

### 8.1 Required Fields

For TSA anchor verification, the following MUST be present:

1. **TSAResponse**: Complete TimeStampToken (DER/base64)
2. **MerkleRoot**: Hash that was submitted to TSA

### 8.2 Verification Algorithm

```python
def verify_tsa_anchor(anchor, event_hash):
    # 1. Decode TSAResponse
    tst = parse_timestamp_token(base64_decode(anchor["TSAResponse"]))
    
    # 2. Extract messageImprint from TST
    message_imprint = tst.tst_info.message_imprint.hashed_message
    
    # 3. Compute expected imprint
    merkle_root_bytes = bytes.fromhex(anchor["MerkleRoot"].replace("sha256:", ""))
    expected_imprint = sha256(merkle_root_bytes)
    
    # 4. Verify match
    if message_imprint != expected_imprint:
        return INVALID
    
    # 5. Verify TSA signature
    if not verify_tsa_signature(tst):
        return INVALID
    
    # 6. Verify Merkle proof (event is in tree)
    if not verify_merkle_proof(event_hash, anchor["MerkleProof"], anchor["MerkleRoot"]):
        return INVALID
    
    return VALID
```

### 8.3 Offline Verification

With TSAResponse included, verification is possible:
- Without network access
- Years after capture
- Without trusting the app developer

---

## 9. Chain Integrity

### 9.1 Hash Chain

Each event links to the previous via PrevHash:

```
Event 1: PrevHash = sha256:0000...0000 (genesis)
Event 2: PrevHash = EventHash(Event 1)
Event 3: PrevHash = EventHash(Event 2)
```

### 9.2 Deletion Detection

When an event is deleted, the chain breaks:

```
Stored:   E1 → E2 → E3 → E4
Deleted:  E1 → E2 → [E3 missing] → E4
Verify:   E4.PrevHash ≠ EventHash(E2) → VIOLATION
```

### 9.3 Tombstone Events

Legitimate deletions create TOMBSTONE events:

```json
{
  "EventType": "TOMBSTONE",
  "DeletedEventId": "event-to-delete",
  "Reason": "USER_REQUEST",
  "DeletedAt": "2026-01-25T12:00:00.000Z"
}
```

---

## 10. Privacy

- **Location**: OFF by default, opt-in per capture
- **SignerInfo**: Optional, user chooses to include
- **Biometric**: Zero data stored, only auth result
- **Crypto-shredding**: GDPR-compliant deletion via TOMBSTONE

---

## 11. Conformance Levels

| Level | TSA | HumanAttestation | SignerInfo |
|-------|-----|------------------|------------|
| Bronze | Optional | Optional | Optional |
| Silver | Per-batch | Optional | Optional |
| Gold | Per-capture | REQUIRED | REQUIRED |

---

## 12. UI Guidelines

| ✅ USE | ❌ AVOID |
|--------|---------|
| "Provenance Available" | "Verified" |
| "Capture Recorded" | "Authenticated" |
| "Self-Attested: {Name}" | "Verified by: {Name}" |
| Information icon (ℹ️) | Checkmark (✓) |

**Required disclosure:**
> "This shows capture provenance. It does NOT verify content truthfulness or signer identity."

---

## 13. References

- RFC 2119 (Requirement Levels)
- RFC 3161 (Time-Stamp Protocol)
- RFC 5652 (CMS)
- RFC 6962 (Certificate Transparency)
- RFC 8785 (JSON Canonicalization Scheme)
- FIPS 186-5 (ECDSA)
- C2PA: https://c2pa.org/specifications/
- VCP: https://github.com/veritaschain/vcp-spec

---

## Appendix A: Migration from v1.0

### A.1 Event Type Mapping

| v1.0 | v1.1 |
|------|------|
| CPP_CAPTURE | INGEST |
| CPP_SEAL | (removed, replaced by batch anchoring) |
| CPP_SHARE | EXPORT |
| CPP_DELETE | TOMBSTONE |

### A.2 Signature Algorithm

v1.0 implementations using Ed25519 remain valid. v1.1 implementations SHOULD use ES256 for mobile platforms.

### A.3 Backward Compatibility

v1.1 verifiers MUST accept:
- Ed25519 signatures (v1.0 compatibility)
- ES256 signatures (v1.1 native)

---

## Appendix B: JSON Schema

See separate file: `cpp-event-schema-v1.1.json`

---

**Copyright © 2026 VeritasChain Standards Organization. CC BY 4.0**
