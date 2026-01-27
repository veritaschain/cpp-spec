# Capture Provenance Profile (CPP) Specification

**Version:** 1.3  
**Status:** Released  
**Date:** 2026-01-27  
**Document ID:** VSO-CPP-SPEC-004  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** CC BY 4.0 International

---

## Abstract

The Capture Provenance Profile (CPP) is an open specification for cryptographically verifiable media capture provenance. Unlike edit-history approaches such as C2PA, CPP focuses on proving "this media was actually captured at this moment" with **deletion detection**, **external timestamping**, and **privacy-by-design** architecture.

CPP v1.3 **fully specifies the Merkle tree construction rules** to ensure deterministic, interoperable implementations. This version defines exact algorithms for leaf hashing, tree construction, proof generation, and verification.

---

## 1. Changes from v1.2

| Item | v1.2 | v1.3 | Rationale |
|------|------|------|-----------|
| **LeafHash computation** | `LeafHash = EventHash` | `LeafHash = SHA256(EventHash)` | Unambiguous leaf definition |
| **LeafHashMethod** | Not specified | REQUIRED field | Explicit algorithm declaration |
| **Pairing rule** | Not specified | `SHA256(Left \|\| Right)` | Deterministic tree construction |
| **Index interpretation** | Not specified | `Even=Left, Odd=Right` | Unambiguous proof verification |
| **Padding rule** | Not specified | `Duplicate last leaf` | Deterministic tree shape |
| **Proof direction** | Not specified | `Bottom to Top` | Consistent proof ordering |

---

## 2. Merkle Tree Construction (NORMATIVE)

### 2.1 Overview

CPP uses a binary Merkle tree following RFC 6962 (Certificate Transparency) conventions with specific adaptations for event hashing.

```
                    Root
                   /    \
                  /      \
               H01        H23
              /   \      /   \
            L0    L1   L2    L3
            |     |    |     |
           E0    E1   E2    E3

Where:
  E0..E3 = Event Hashes (input)
  L0..L3 = Leaf Hashes = SHA256(Ei)
  H01    = SHA256(L0 || L1)
  H23    = SHA256(L2 || L3)
  Root   = SHA256(H01 || H23)
```

### 2.2 Leaf Hash Computation (NORMATIVE)

**Definition:**

```
LeafHash = SHA256(EventHash_bytes)
```

**Where:**
- `EventHash_bytes` = 32-byte binary representation of EventHash
- EventHash format is `sha256:<64_hex_chars>`
- Strip the `sha256:` prefix before converting to bytes

**Algorithm:**

```python
def compute_leaf_hash(event_hash: str) -> str:
    """
    Compute LeafHash from EventHash per CPP v1.3
    
    Args:
        event_hash: "sha256:abc123..." format
    Returns:
        "sha256:def456..." format
    """
    # Step 1: Extract hex portion
    hex_str = event_hash.replace("sha256:", "")
    
    # Step 2: Convert to bytes
    event_hash_bytes = bytes.fromhex(hex_str)  # 32 bytes
    
    # Step 3: Compute SHA-256
    leaf_hash_bytes = sha256(event_hash_bytes)
    
    # Step 4: Format result
    return "sha256:" + leaf_hash_bytes.hex()
```

**Rationale:**
- Prevents second preimage attacks
- Ensures leaf hashes are distinct from internal node hashes
- Follows RFC 6962 conventions

### 2.3 Tree Construction Algorithm (NORMATIVE)

**Step 1: Compute Leaf Hashes**

```python
leaf_hashes = [compute_leaf_hash(eh) for eh in event_hashes]
```

**Step 2: Pad to Power of 2**

If `len(leaf_hashes)` is not a power of 2, duplicate the last element until it is:

```python
def pad_to_power_of_2(leaves: list[str]) -> list[str]:
    """
    Pad leaf array by duplicating last element
    
    Examples:
        [A]       -> [A]           (already 2^0)
        [A,B]     -> [A,B]         (already 2^1)
        [A,B,C]   -> [A,B,C,C]     (pad to 2^2)
        [A,B,C,D,E] -> [A,B,C,D,E,E,E,E]  (pad to 2^3)
    """
    n = len(leaves)
    if n == 0:
        return []
    
    # Find next power of 2
    target = 1
    while target < n:
        target *= 2
    
    # Duplicate last element
    padded = leaves.copy()
    while len(padded) < target:
        padded.append(padded[-1])
    
    return padded
```

**IMPORTANT:** The padding elements are NOT counted in `TreeSize`. TreeSize represents the original number of leaves.

**Step 3: Build Tree Levels**

```python
def build_tree_levels(padded_leaves: list[str]) -> list[list[str]]:
    """
    Build all tree levels from bottom to top
    
    Returns:
        List of levels, where levels[0] = leaves, levels[-1] = [root]
    """
    levels = [padded_leaves]
    current = padded_leaves
    
    while len(current) > 1:
        next_level = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1]
            parent = compute_parent_hash(left, right)
            next_level.append(parent)
        levels.append(next_level)
        current = next_level
    
    return levels
```

**Step 4: Compute Parent Hash**

```python
def compute_parent_hash(left: str, right: str) -> str:
    """
    Compute parent node hash from two children
    
    ParentHash = SHA256(Left_bytes || Right_bytes)
    """
    left_bytes = bytes.fromhex(left.replace("sha256:", ""))
    right_bytes = bytes.fromhex(right.replace("sha256:", ""))
    
    combined = left_bytes + right_bytes  # 64 bytes total
    parent_bytes = sha256(combined)
    
    return "sha256:" + parent_bytes.hex()
```

### 2.4 Proof Generation (NORMATIVE)

**Definition:** A Merkle proof for leaf at index `i` consists of sibling hashes from bottom to top.

```python
def generate_proof(leaf_index: int, levels: list[list[str]]) -> list[str]:
    """
    Generate Merkle proof for a specific leaf
    
    Args:
        leaf_index: 0-based index in original (unpadded) leaves
        levels: Tree levels from build_tree_levels()
    
    Returns:
        List of sibling hashes, bottom to top
    """
    proof = []
    index = leaf_index
    
    # Traverse from leaf level to root (exclude root level)
    for level in range(len(levels) - 1):
        level_nodes = levels[level]
        
        # Find sibling index
        if index % 2 == 0:
            sibling_index = index + 1  # Sibling is to the right
        else:
            sibling_index = index - 1  # Sibling is to the left
        
        # Add sibling to proof
        if sibling_index < len(level_nodes):
            proof.append(level_nodes[sibling_index])
        
        # Move to parent index
        index = index // 2
    
    return proof
```

### 2.5 Proof Verification (NORMATIVE)

**Algorithm:**

```python
def verify_merkle_proof(
    event_hash: str,
    leaf_index: int,
    proof: list[str],
    expected_root: str,
    tree_size: int
) -> bool:
    """
    Verify a Merkle proof per CPP v1.3
    
    Args:
        event_hash: The EventHash to verify
        leaf_index: Position in the tree (0-based)
        proof: Array of sibling hashes (bottom to top)
        expected_root: The expected MerkleRoot
        tree_size: Original number of leaves
    
    Returns:
        True if verification passes
    """
    # Step 1: Compute leaf hash
    current_hash = compute_leaf_hash(event_hash)
    
    # Step 2: Traverse proof from bottom to top
    index = leaf_index
    
    for sibling_hash in proof:
        # Determine order based on current index
        # Even index = current is LEFT child
        # Odd index = current is RIGHT child
        
        if index % 2 == 0:
            # Current is left, sibling is right
            current_hash = compute_parent_hash(current_hash, sibling_hash)
        else:
            # Current is right, sibling is left
            current_hash = compute_parent_hash(sibling_hash, current_hash)
        
        # Move to parent index
        index = index // 2
    
    # Step 3: Compare with expected root
    return current_hash.lower() == expected_root.lower()
```

### 2.6 Index Interpretation Rule (NORMATIVE)

**Rule:** The parity of the current index determines the position:

| Index | Position | Pairing Order |
|-------|----------|---------------|
| Even (0, 2, 4, ...) | Left child | `hash(current \|\| sibling)` |
| Odd (1, 3, 5, ...) | Right child | `hash(sibling \|\| current)` |

**Example:**

```
Tree:         Root
             /    \
           H01    H23
          /  \   /  \
         L0  L1 L2  L3

Index 0 (even): L0 is LEFT, sibling L1 is RIGHT
  -> H01 = SHA256(L0 || L1)

Index 1 (odd): L1 is RIGHT, sibling L0 is LEFT
  -> H01 = SHA256(L0 || L1)

Index 2 (even): L2 is LEFT, sibling L3 is RIGHT
  -> H23 = SHA256(L2 || L3)
```

---

## 3. Single-Leaf Merkle Tree (NORMATIVE)

### 3.1 When TreeSize = 1

When a single event is anchored (most common case), the following rules MUST apply:

```
TreeSize    = 1
LeafIndex   = 0
Proof       = []  (empty array)
LeafHash    = SHA256(EventHash)
Root        = LeafHash
```

**Validation requirement:** If any of these conditions are violated, the anchor is INVALID.

### 3.2 Single-Leaf Verification

```python
def verify_single_leaf(
    event_hash: str,
    anchor: dict
) -> bool:
    """
    Verify a single-leaf Merkle tree
    """
    merkle = anchor["Merkle"]
    
    # Validate structure
    if merkle["TreeSize"] != 1:
        return False
    if merkle["LeafIndex"] != 0:
        return False
    if merkle["Proof"] != []:
        return False
    
    # Compute expected values
    expected_leaf = compute_leaf_hash(event_hash)
    
    # Verify LeafHash
    if merkle["LeafHash"].lower() != expected_leaf.lower():
        return False
    
    # Verify Root == LeafHash
    if merkle["Root"].lower() != expected_leaf.lower():
        return False
    
    return True
```

---

## 4. Anchor Data Model (NORMATIVE)

### 4.1 JSON Schema

```json
{
  "Anchor": {
    "AnchorID": "uuid",
    "AnchorType": "RFC3161",
    
    "AnchorDigest": "abc123...def",
    "AnchorDigestAlgorithm": "sha-256",
    
    "Merkle": {
      "TreeSize": 1,
      "LeafHashMethod": "SHA256(EventHash)",
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
      "GenTime": "2026-01-27T10:31:00.000Z",
      "Service": "https://rfc3161.ai.moda"
    }
  }
}
```

### 4.2 Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| AnchorID | string | REQUIRED | Unique anchor identifier |
| AnchorType | string | REQUIRED | Always "RFC3161" |
| AnchorDigest | string | REQUIRED | 32-byte hex, TSA input value |
| AnchorDigestAlgorithm | string | REQUIRED | Always "sha-256" |
| Merkle.TreeSize | integer | REQUIRED | Number of original leaves (before padding) |
| **Merkle.LeafHashMethod** | string | **REQUIRED (v1.3)** | **Always "SHA256(EventHash)"** |
| Merkle.LeafHash | string | REQUIRED | Computed LeafHash with sha256: prefix |
| Merkle.LeafIndex | integer | REQUIRED | Position in tree (0-based) |
| Merkle.Proof | array | REQUIRED | Sibling hashes for verification |
| Merkle.Root | string | REQUIRED | Merkle root hash |
| TSA.Token | string | REQUIRED | RFC3161 TimeStampToken (DER/base64) |
| TSA.MessageImprint | object | REQUIRED | Extracted from TST |
| TSA.GenTime | ISO8601 | REQUIRED | Timestamp from TST |
| TSA.Service | string | REQUIRED | TSA endpoint URL |

### 4.3 AnchorDigest Computation

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

## 5. TSA Anchoring Specification (NORMATIVE)

### 5.1 Core Requirements

**Three mandatory requirements for TSA anchoring:**

1. **TSA input is AnchorDigest ONLY** - No other values may be submitted to TSA
2. **AnchorDigest MUST equal MerkleRoot** - The 32-byte hash submitted to TSA
3. **TSAResponse.messageImprint.hashedMessage MUST equal AnchorDigest** - Verification required

### 5.2 RFC 3161 TimeStampReq

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

### 5.3 TSA Response Verification

```python
def verify_tsa_anchor(event_hash: str, anchor: dict) -> VerificationResult:
    """
    Complete TSA anchor verification per CPP v1.3
    """
    
    # Step 1: Validate Merkle structure
    merkle = anchor["Merkle"]
    tree_size = merkle["TreeSize"]
    
    if tree_size == 1:
        if not verify_single_leaf(event_hash, anchor):
            return INVALID("Single-leaf Merkle validation failed")
    else:
        if not verify_merkle_proof(
            event_hash,
            merkle["LeafIndex"],
            merkle["Proof"],
            merkle["Root"],
            tree_size
        ):
            return INVALID("Merkle proof verification failed")
    
    # Step 2: Validate LeafHashMethod (v1.3)
    leaf_hash_method = merkle.get("LeafHashMethod", "SHA256(EventHash)")
    if leaf_hash_method != "SHA256(EventHash)":
        return INVALID(f"Unsupported LeafHashMethod: {leaf_hash_method}")
    
    # Step 3: AnchorDigest validation
    anchor_digest = anchor["AnchorDigest"]
    expected_digest = merkle["Root"].replace("sha256:", "")
    
    if anchor_digest.lower() != expected_digest.lower():
        return INVALID("AnchorDigest != MerkleRoot")
    
    # Step 4: Decode TSAResponse
    tsa_token = base64_decode(anchor["TSA"]["Token"])
    tst = parse_timestamp_token(tsa_token)
    
    # Step 5: Extract messageImprint from TST
    tst_message_imprint = tst.tst_info.message_imprint.hashed_message
    tst_hash_algorithm = tst.tst_info.message_imprint.hash_algorithm
    
    # Step 6: Verify hash algorithm is SHA-256
    if tst_hash_algorithm != "sha-256":
        return INVALID(f"Unsupported hash algorithm: {tst_hash_algorithm}")
    
    # Step 7: Verify messageImprint == AnchorDigest
    if tst_message_imprint.hex().lower() != anchor_digest.lower():
        return INVALID("TSA messageImprint != AnchorDigest")
    
    # Step 8: Cross-check stored messageImprint (if present)
    if "MessageImprint" in anchor["TSA"]:
        stored_imprint = anchor["TSA"]["MessageImprint"]["HashedMessage"]
        if stored_imprint.lower() != tst_message_imprint.hex().lower():
            return WARNING("Stored messageImprint inconsistent with TST")
    
    # Step 9: TSA signature verification (RECOMMENDED)
    # This requires TSA certificate chain validation
    
    # Step 10: Extract and return genTime
    gen_time = tst.tst_info.gen_time
    
    return VALID(gen_time=gen_time)
```

### 5.4 Verification Checklist

| # | Check | Expected | If Failed |
|---|-------|----------|-----------|
| 1 | TreeSize == 1 implies LeafIndex == 0 | True | INVALID |
| 2 | TreeSize == 1 implies Proof == [] | True | INVALID |
| 3 | TreeSize == 1 implies Root == LeafHash | True | INVALID |
| 4 | LeafHash == SHA256(EventHash) | True | INVALID |
| 5 | LeafHashMethod == "SHA256(EventHash)" | True | INVALID |
| 6 | AnchorDigest == MerkleRoot (hex) | True | INVALID |
| 7 | TSA hashAlgorithm == sha-256 | True | INVALID |
| 8 | TSA messageImprint == AnchorDigest | True | INVALID |
| 9 | Stored MessageImprint matches TST | True | WARNING |

---

## 6. Export Format (Shareable)

### 6.1 Verification Pack

```json
{
  "proof_version": "1.3",
  "proof_type": "CPP_INGEST_PROOF",
  "proof_id": "01932f5a-7b8c-7def-8abc-123456789012",
  
  "event": {
    "event_id": "...",
    "event_type": "INGEST",
    "timestamp": "2026-01-27T10:30:00.000Z",
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
      "leaf_hash_method": "SHA256(EventHash)",
      "leaf_hash": "sha256:...",
      "leaf_index": 0,
      "proof": [],
      "root": "sha256:..."
    },
    
    "tsa": {
      "token": "base64:MIAGCSqGSIb3DQEHAqCAMIACAQEx...",
      "message_imprint": "abc123...def",
      "gen_time": "2026-01-27T10:31:00.000Z",
      "service": "https://rfc3161.ai.moda"
    }
  },
  
  "attested": true
}
```

---

## 7. Multi-Leaf Batch Anchoring

### 7.1 Use Case

When multiple events are captured in rapid succession, they may be anchored together in a single TSA request for efficiency.

### 7.2 Batch Construction

```python
def create_batch_anchor(event_hashes: list[str]) -> BatchAnchorResult:
    """
    Create a batch anchor for multiple events
    
    Each event gets its own Merkle proof to verify inclusion
    """
    # Build tree
    tree_result = build_merkle_tree(event_hashes)
    
    # Create individual anchors
    anchors = []
    for i, event_hash in enumerate(event_hashes):
        anchor = {
            "AnchorID": generate_uuid(),
            "AnchorType": "RFC3161",
            "AnchorDigest": tree_result.root.replace("sha256:", ""),
            "AnchorDigestAlgorithm": "sha-256",
            "Merkle": {
                "TreeSize": len(event_hashes),
                "LeafHashMethod": "SHA256(EventHash)",
                "LeafHash": tree_result.leaf_proofs[i].leaf_hash,
                "LeafIndex": i,
                "Proof": tree_result.leaf_proofs[i].proof,
                "Root": tree_result.root
            }
        }
        anchors.append(anchor)
    
    return BatchAnchorResult(
        root=tree_result.root,
        anchors=anchors
    )
```

### 7.3 Batch Verification Example

```
TreeSize = 5, LeafIndex = 3

Tree structure (padded to 8):
         Root
        /    \
      H03      H47
     /   \    /   \
   H01  H23  H45  H67
   / \  / \  / \  / \
  L0 L1 L2 L3 L4 L5 L6 L7
              ^
              Event at index 3

Proof for index 3: [L2, H01, H47]  (bottom to top)

Verification:
  1. current = L3 (leaf hash of event 3)
  2. index=3 is ODD -> current is RIGHT
     current = SHA256(L2 || current) = H23
     index = 3 // 2 = 1
  3. index=1 is ODD -> current is RIGHT
     current = SHA256(H01 || current) = H03
     index = 1 // 2 = 0
  4. index=0 is EVEN -> current is LEFT
     current = SHA256(current || H47) = Root
  5. Compare with expected Root -> VALID
```

---

## 8. Backward Compatibility

### 8.1 Reading v1.2 Proofs

v1.3 verifiers encountering v1.2 proofs (without LeafHashMethod field) SHOULD:

1. Assume LeafHashMethod = "SHA256(EventHash)"
2. Proceed with verification

### 8.2 Reading v1.1 Proofs

v1.3 verifiers encountering v1.1 proofs (without AnchorDigest or MessageImprint) SHOULD:

1. Compute AnchorDigest from MerkleRoot
2. Extract messageImprint from TSAResponse if present
3. Perform verification with WARNING status if messageImprint cannot be verified

### 8.3 Version Detection

| Field Present | Version |
|---------------|---------|
| LeafHashMethod | v1.3+ |
| AnchorDigest + TSA.MessageImprint (no LeafHashMethod) | v1.2 |
| MerkleRoot only | v1.1 or earlier |

---

## 9. Security Considerations

### 9.1 Why LeafHash = SHA256(EventHash)

**Without the additional hash:**
- Leaf hashes could collide with internal node hashes
- Enables second preimage attacks on the tree

**With SHA256(EventHash):**
- Leaf domain is separated from internal node domain
- Matches RFC 6962 security model

### 9.2 Why Padding Uses Duplication

**Duplicate-last-leaf padding:**
- Deterministic (no randomness)
- Same events always produce same tree
- Verifiable without knowledge of padding rule

**Alternatives considered but rejected:**
- Zero-padding: Different hash, tree structure ambiguity
- Random padding: Non-deterministic, verification issues

### 9.3 Why Proof Order is Bottom-to-Top

**Bottom-to-top ordering:**
- Matches traversal order during verification
- Natural index evolution (divide by 2 each level)
- Consistent with RFC 6962

---

## 10. Conformance

### 10.1 Producer Requirements

A CPP v1.3 producer MUST:

1. Compute LeafHash as SHA256(EventHash)
2. Set LeafHashMethod = "SHA256(EventHash)"
3. Use duplicate-last-leaf padding for non-power-of-2 tree sizes
4. Generate proofs in bottom-to-top order
5. Set AnchorDigest equal to MerkleRoot (hex, no prefix)
6. Submit only AnchorDigest to TSA
7. Extract and store TSA.MessageImprint from response
8. Set TreeSize to original leaf count (before padding)

### 10.2 Verifier Requirements

A CPP v1.3 verifier MUST:

1. Validate LeafHashMethod is "SHA256(EventHash)"
2. Compute LeafHash as SHA256(EventHash)
3. Apply even=left, odd=right rule for proof traversal
4. Validate single-leaf rules when TreeSize == 1
5. Verify Merkle proof produces expected Root
6. Verify AnchorDigest == MerkleRoot
7. Extract messageImprint from TSAResponse
8. Verify messageImprint == AnchorDigest
9. Report INVALID if any check fails

---

## Appendix A: Changes from v1.2

### A.1 New Required Fields

| Field | Location | Type | Description |
|-------|----------|------|-------------|
| LeafHashMethod | Anchor.Merkle | string | Always "SHA256(EventHash)" |

### A.2 New Normative Requirements

1. LeafHash computation: SHA256(EventHash_bytes)
2. Pairing rule: SHA256(Left || Right)
3. Index interpretation: Even=Left, Odd=Right
4. Padding rule: Duplicate last leaf
5. Proof ordering: Bottom to top

### A.3 Clarifications

1. TreeSize is original count (before padding)
2. Proof array contains sibling hashes only
3. Verification traverses from leaf to root

---

## Appendix B: Reference Implementation

### B.1 Python

```python
import hashlib

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def compute_leaf_hash(event_hash: str) -> str:
    hex_str = event_hash.replace("sha256:", "")
    event_hash_bytes = bytes.fromhex(hex_str)
    leaf_hash_bytes = sha256(event_hash_bytes)
    return "sha256:" + leaf_hash_bytes.hex()

def compute_parent_hash(left: str, right: str) -> str:
    left_bytes = bytes.fromhex(left.replace("sha256:", ""))
    right_bytes = bytes.fromhex(right.replace("sha256:", ""))
    parent_bytes = sha256(left_bytes + right_bytes)
    return "sha256:" + parent_bytes.hex()

def verify_merkle_proof(
    event_hash: str,
    leaf_index: int,
    proof: list[str],
    expected_root: str
) -> bool:
    current_hash = compute_leaf_hash(event_hash)
    index = leaf_index
    
    for sibling_hash in proof:
        if index % 2 == 0:
            current_hash = compute_parent_hash(current_hash, sibling_hash)
        else:
            current_hash = compute_parent_hash(sibling_hash, current_hash)
        index //= 2
    
    return current_hash.lower() == expected_root.lower()
```

### B.2 Swift

```swift
import CryptoKit

func computeLeafHash(_ eventHash: String) -> String {
    let hexStr = eventHash.replacingOccurrences(of: "sha256:", with: "")
    let eventHashBytes = Data(hexString: hexStr)!
    let leafHash = SHA256.hash(data: eventHashBytes)
    return "sha256:" + leafHash.hexString
}

func computeParentHash(left: String, right: String) -> String {
    let leftBytes = Data(hexString: left.replacingOccurrences(of: "sha256:", with: ""))!
    let rightBytes = Data(hexString: right.replacingOccurrences(of: "sha256:", with: ""))!
    var combined = leftBytes
    combined.append(rightBytes)
    let parentHash = SHA256.hash(data: combined)
    return "sha256:" + parentHash.hexString
}

func verifyMerkleProof(
    eventHash: String,
    leafIndex: Int,
    proof: [String],
    expectedRoot: String
) -> Bool {
    var currentHash = computeLeafHash(eventHash)
    var index = leafIndex
    
    for siblingHash in proof {
        if index % 2 == 0 {
            currentHash = computeParentHash(left: currentHash, right: siblingHash)
        } else {
            currentHash = computeParentHash(left: siblingHash, right: currentHash)
        }
        index /= 2
    }
    
    return currentHash.lowercased() == expectedRoot.lowercased()
}
```

---

## Appendix C: Test Vectors

### C.1 Single-Leaf Tree

```
Input:
  EventHash = "sha256:4e3a6f9c8d7b2a1e5f0c3d8b7a6e5f4c3d2b1a0e9f8d7c6b5a4e3d2c1b0a9f8e"

Expected:
  LeafHash = SHA256(bytes.fromhex("4e3a6f...")) 
           = "sha256:9a7923adcc54cec58393992be0637a0b89c0882676cfbeeec4fa1c6182bf4709"
  
  TreeSize = 1
  LeafIndex = 0
  Proof = []
  Root = LeafHash
  AnchorDigest = "9a7923adcc54cec58393992be0637a0b89c0882676cfbeeec4fa1c6182bf4709"
```

### C.2 Two-Leaf Tree

```
Input:
  EventHash[0] = "sha256:aaaa..."
  EventHash[1] = "sha256:bbbb..."

Expected:
  L0 = SHA256(bytes.fromhex("aaaa..."))
  L1 = SHA256(bytes.fromhex("bbbb..."))
  Root = SHA256(L0 || L1)
  
  TreeSize = 2
  
  For index 0: Proof = [L1]
  For index 1: Proof = [L0]
```

### C.3 Five-Leaf Tree (Padded)

```
Input:
  EventHash[0..4] = [E0, E1, E2, E3, E4]

Padded to 8:
  [L0, L1, L2, L3, L4, L4, L4, L4]
  
TreeSize = 5 (original count)

For index 3:
  Proof = [L2, H01, H47]
  
  Where:
    L2 = SHA256(E2)
    H01 = SHA256(L0 || L1)
    H47 = SHA256(H45 || H67)
```

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
