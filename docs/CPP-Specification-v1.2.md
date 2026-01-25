# Capture Provenance Profile (CPP) Specification

**Version:** 1.2  
**Status:** Release Candidate  
**Date:** 2026-01-25  
**Document ID:** VSO-CPP-SPEC-003  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** CC BY 4.0 International

---

## Abstract

The Capture Provenance Profile (CPP) is an open specification for cryptographically verifiable media capture provenance. Unlike edit-history approaches such as C2PA, CPP focuses on proving "this media was actually captured at this moment" with **deletion detection**, **external timestamping**, and **privacy-by-design** architecture.

CPP v1.2 clarifies the **TSA anchoring specification** to ensure unambiguous third-party verification. This version defines exact requirements for `AnchorDigest`, `messageImprint` verification, and single-leaf Merkle tree handling.

---

## 1. Changes from v1.1

| Item | v1.1 | v1.2 | Rationale |
|------|------|------|-----------|
| **AnchorDigest** | Implicit | REQUIRED explicit field | Unambiguous TSA input |
| **TSA messageImprint** | Not verified | REQUIRED verification | Third-party verifiability |
| **Single-leaf Merkle** | Implicit rules | Explicit specification | No JSON contradictions |
| **TreeSize** | Not specified | REQUIRED field | Validation requirement |

---

## 2. TSA Anchoring Specification (NORMATIVE)

### 2.1 Core Requirements

**Three mandatory requirements for TSA anchoring:**

1. **TSA input is AnchorDigest ONLY** - No other values may be submitted to TSA
2. **AnchorDigest MUST equal MerkleRoot** - The 32-byte hash submitted to TSA
3. **TSAResponse.messageImprint.hashedMessage MUST equal AnchorDigest** - Verification required

### 2.2 Anchor Data Model

```json
{
  "Anchor": {
    "AnchorID": "uuid",
    "AnchorType": "RFC3161",
    
    "AnchorDigest": "abc123...def",
    "AnchorDigestAlgorithm": "sha-256",
    
    "Merkle": {
      "TreeSize": 1,
      "LeafHash": "sha256:abc123...",
      "LeafIndex": 0,
      "Proof": [],
      "Root": "sha256:abc123..."
    },
    
    "TSA": {
      "Token": "base64:MIAGCSqGSIb3DQEHAqCAMIACAQEx...",
      "MessageImprint": {
        "HashAlgorithm": "sha-256",
        "HashedMessage": "abc123...def"
      },
      "GenTime": "2026-01-25T10:31:00.000Z",
      "Service": "https://rfc3161.ai.moda"
    }
  }
}
```

### 2.3 Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| AnchorID | string | REQUIRED | Unique anchor identifier |
| AnchorType | string | REQUIRED | Always "RFC3161" |
| **AnchorDigest** | string | **REQUIRED** | **32-byte hex, TSA input value** |
| **AnchorDigestAlgorithm** | string | **REQUIRED** | **Always "sha-256"** |
| Merkle.TreeSize | integer | REQUIRED | Number of leaves in tree |
| Merkle.LeafHash | string | REQUIRED | EventHash with sha256: prefix |
| Merkle.LeafIndex | integer | REQUIRED | Position in tree (0-based) |
| Merkle.Proof | array | REQUIRED | Sibling hashes for verification |
| Merkle.Root | string | REQUIRED | Merkle root hash |
| TSA.Token | string | REQUIRED | RFC3161 TimeStampToken (DER/base64) |
| **TSA.MessageImprint** | object | **REQUIRED** | **Extracted from TST** |
| TSA.GenTime | ISO8601 | REQUIRED | Timestamp from TST |
| TSA.Service | string | REQUIRED | TSA endpoint URL |

---

## 3. Single-Leaf Merkle Tree (NORMATIVE)

### 3.1 When TreeSize = 1

When a single event is anchored (most common case), the following rules MUST apply:

```
TreeSize    = 1
LeafIndex   = 0
Proof       = []  (empty array)
Root        = LeafHash = EventHash
```

**Validation requirement:** If any of these conditions are violated, the anchor is INVALID.

### 3.2 Relationship Between MerkleRoot and EventHash

```
LeafHash   = EventHash                    (definition)
MerkleRoot = merkle_root(LeafHash[])      (computation)

For single-leaf:  MerkleRoot == LeafHash == EventHash
For multi-leaf:   MerkleRoot != EventHash (requires Proof)
```

### 3.3 AnchorDigest Computation

```python
# AnchorDigest is the RAW BYTES of MerkleRoot (32 bytes)
# NOT a hash of the hash, NOT a string encoding

merkle_root = "sha256:abc123def456..."
anchor_digest = merkle_root.replace("sha256:", "")  # 64 hex chars = 32 bytes
```

**PROHIBITED:**
- `sha256(merkle_root_string)` - Double hashing
- `sha256(merkle_root_bytes)` - Double hashing
- String encoding of hex before hashing

---

## 4. TSA Request Format (NORMATIVE)

### 4.1 RFC 3161 TimeStampReq

```asn1
TimeStampReq ::= SEQUENCE {
   version         INTEGER { v1(1) },
   messageImprint  MessageImprint,
   certReq         BOOLEAN DEFAULT FALSE
}

MessageImprint ::= SEQUENCE {
   hashAlgorithm   AlgorithmIdentifier,  -- MUST be SHA-256
   hashedMessage   OCTET STRING          -- MUST be AnchorDigest (32 bytes)
}
```

### 4.2 Implementation

```python
def create_tsa_request(anchor_digest: str) -> bytes:
    # anchor_digest is 64 hex characters (32 bytes)
    hash_bytes = bytes.fromhex(anchor_digest)
    
    # Build ASN.1 structure
    sha256_oid = bytes([0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])
    
    # MessageImprint = SEQUENCE { hashAlgorithm, hashedMessage }
    message_imprint = build_sequence([
        build_sequence([sha256_oid]),  # AlgorithmIdentifier
        build_octet_string(hash_bytes)  # hashedMessage
    ])
    
    # TimeStampReq = SEQUENCE { version, messageImprint, certReq }
    return build_sequence([
        build_integer(1),      # version
        message_imprint,
        build_boolean(True)    # certReq
    ])
```

---

## 5. TSA Response Verification (NORMATIVE)

### 5.1 Verification Algorithm

```python
def verify_tsa_anchor(event_hash: str, anchor: dict) -> VerificationResult:
    """
    Complete TSA anchor verification per CPP v1.2
    
    Returns: VALID, INVALID, or WARNING
    """
    
    # Step 1: Single-leaf Merkle validation
    tree_size = anchor["Merkle"]["TreeSize"]
    leaf_hash = anchor["Merkle"]["LeafHash"]
    merkle_root = anchor["Merkle"]["Root"]
    
    if tree_size == 1:
        # Single-leaf: Root == LeafHash == EventHash
        if anchor["Merkle"]["LeafIndex"] != 0:
            return INVALID("LeafIndex must be 0 for single-leaf")
        if anchor["Merkle"]["Proof"] != []:
            return INVALID("Proof must be empty for single-leaf")
        if merkle_root != leaf_hash:
            return INVALID("Root != LeafHash for single-leaf")
        if merkle_root != event_hash:
            return INVALID("Root != EventHash for single-leaf")
    else:
        # Multi-leaf: Verify Merkle proof
        if not verify_merkle_proof(
            leaf_hash,
            anchor["Merkle"]["LeafIndex"],
            anchor["Merkle"]["Proof"],
            merkle_root
        ):
            return INVALID("Merkle proof verification failed")
    
    # Step 2: AnchorDigest validation
    anchor_digest = anchor["AnchorDigest"]
    expected_digest = merkle_root.replace("sha256:", "")
    
    if anchor_digest.lower() != expected_digest.lower():
        return INVALID("AnchorDigest != MerkleRoot")
    
    # Step 3: Decode TSAResponse
    tsa_token = base64_decode(anchor["TSA"]["Token"])
    tst = parse_timestamp_token(tsa_token)
    
    # Step 4: Extract messageImprint from TST
    tst_message_imprint = tst.tst_info.message_imprint.hashed_message
    tst_hash_algorithm = tst.tst_info.message_imprint.hash_algorithm
    
    # Step 5: Verify hash algorithm is SHA-256
    if tst_hash_algorithm != "sha-256":
        return INVALID(f"Unsupported hash algorithm: {tst_hash_algorithm}")
    
    # Step 6: Verify messageImprint == AnchorDigest
    if tst_message_imprint.hex().lower() != anchor_digest.lower():
        return INVALID("TSA messageImprint != AnchorDigest")
    
    # Step 7: Cross-check stored messageImprint (if present)
    if "MessageImprint" in anchor["TSA"]:
        stored_imprint = anchor["TSA"]["MessageImprint"]["HashedMessage"]
        if stored_imprint.lower() != tst_message_imprint.hex().lower():
            return WARNING("Stored messageImprint inconsistent with TST")
    
    # Step 8: TSA signature verification (optional but recommended)
    # This requires TSA certificate chain validation
    
    # Step 9: Extract and return genTime
    gen_time = tst.tst_info.gen_time
    
    return VALID(gen_time=gen_time)
```

### 5.2 Verification Checklist

| # | Check | Expected | If Failed |
|---|-------|----------|-----------|
| 1 | TreeSize == 1 implies LeafIndex == 0 | True | INVALID |
| 2 | TreeSize == 1 implies Proof == [] | True | INVALID |
| 3 | TreeSize == 1 implies Root == LeafHash | True | INVALID |
| 4 | TreeSize == 1 implies Root == EventHash | True | INVALID |
| 5 | AnchorDigest == MerkleRoot (hex) | True | INVALID |
| 6 | TSA hashAlgorithm == sha-256 | True | INVALID |
| 7 | TSA messageImprint == AnchorDigest | True | INVALID |
| 8 | Stored MessageImprint matches TST | True | WARNING |

---

## 6. Export Format (Shareable)

### 6.1 Verification Pack

```json
{
  "proof_version": "1.2",
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
    "anchor_digest": "abc123...def",
    "digest_algorithm": "sha-256",
    
    "merkle": {
      "tree_size": 1,
      "leaf_index": 0,
      "proof": [],
      "root": "sha256:..."
    },
    
    "tsa": {
      "token": "base64:MIAGCSqGSIb3DQEHAqCAMIACAQEx...",
      "message_imprint": "abc123...def",
      "gen_time": "2026-01-25T10:31:00.000Z",
      "service": "https://rfc3161.ai.moda"
    }
  },
  
  "attested": true
}
```

---

## 7. Backward Compatibility

### 7.1 Reading v1.1 Proofs

v1.2 verifiers encountering v1.1 proofs (without AnchorDigest or MessageImprint fields) SHOULD:

1. Compute AnchorDigest from MerkleRoot
2. Extract messageImprint from TSAResponse if present
3. Perform verification with WARNING status if messageImprint cannot be verified

### 7.2 Version Detection

| Field Present | Version |
|---------------|---------|
| AnchorDigest + TSA.MessageImprint | v1.2+ |
| MerkleRoot only | v1.1 or earlier |

---

## 8. Security Considerations

### 8.1 Why AnchorDigest Must Equal MerkleRoot

If AnchorDigest ≠ MerkleRoot, an attacker could:
1. Submit arbitrary data to TSA
2. Claim the TSA timestamp applies to different events
3. Break the binding between events and timestamps

### 8.2 Why messageImprint Verification is Mandatory

Without messageImprint verification:
1. TSAResponse could be swapped between anchors
2. Third parties cannot confirm what TSA actually signed
3. Timestamp claims become unverifiable

---

## 9. Implementation Notes

### 9.1 ASN.1 Parsing for messageImprint

```python
def extract_message_imprint(tsa_token: bytes) -> tuple[str, bytes]:
    """
    Extract hashAlgorithm and hashedMessage from TST
    
    TSTInfo ::= SEQUENCE {
        version         INTEGER,
        policy          OBJECT IDENTIFIER,
        messageImprint  MessageImprint,  <-- target
        ...
    }
    
    MessageImprint ::= SEQUENCE {
        hashAlgorithm   AlgorithmIdentifier,
        hashedMessage   OCTET STRING
    }
    """
    # Parse ContentInfo -> SignedData -> encapContentInfo -> TSTInfo
    # Extract messageImprint SEQUENCE
    # Return (hash_algorithm_oid, hashed_message_bytes)
    pass
```

### 9.2 Database Schema (Reference)

```sql
CREATE TABLE anchors (
    anchor_id TEXT PRIMARY KEY,
    anchor_type TEXT NOT NULL DEFAULT 'RFC3161',
    
    -- Merkle Tree
    merkle_root TEXT NOT NULL,
    tree_size INTEGER NOT NULL DEFAULT 1,
    
    -- TSA Anchor
    anchor_digest TEXT NOT NULL,
    anchor_digest_algorithm TEXT NOT NULL DEFAULT 'sha-256',
    tsa_token BLOB,
    tsa_message_imprint TEXT,  -- Extracted from TST
    tsa_gen_time TEXT,
    tsa_service TEXT,
    
    -- Metadata
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

-- Validation: anchor_digest should equal merkle_root (without prefix)
-- Validation: tsa_message_imprint should equal anchor_digest
```

---

## 10. Conformance

### 10.1 Producer Requirements

A CPP v1.2 producer MUST:
1. Set AnchorDigest equal to MerkleRoot (hex, no prefix)
2. Submit only AnchorDigest to TSA
3. Extract and store TSA.MessageImprint from response
4. Set TreeSize accurately

### 10.2 Verifier Requirements

A CPP v1.2 verifier MUST:
1. Validate single-leaf Merkle rules when TreeSize == 1
2. Verify AnchorDigest == MerkleRoot
3. Extract messageImprint from TSAResponse
4. Verify messageImprint == AnchorDigest
5. Report INVALID if any check fails

---

## Appendix A: Changes from v1.1

### A.1 New Required Fields

| Field | Location | Type | Description |
|-------|----------|------|-------------|
| AnchorDigest | Anchor | string | TSA input value |
| AnchorDigestAlgorithm | Anchor | string | Always "sha-256" |
| TreeSize | Anchor.Merkle | integer | Leaf count |
| MessageImprint | Anchor.TSA | object | From TST |

### A.2 New Validation Requirements

1. Single-leaf Merkle tree rules
2. AnchorDigest == MerkleRoot
3. messageImprint == AnchorDigest

---

## References

- RFC 2119 (Requirement Levels)
- RFC 3161 (Time-Stamp Protocol)
- RFC 5652 (CMS)
- RFC 6962 (Certificate Transparency - Merkle Trees)
- RFC 8785 (JSON Canonicalization Scheme)
- FIPS 186-5 (ECDSA)

---

**Copyright © 2026 VeritasChain Standards Organization. CC BY 4.0**
