# CPP-C2PA Interoperability Guide

## Overview

CPP (Capture Provenance Profile) is designed to **complement** C2PA, not replace it.

| Aspect | C2PA | CPP |
|--------|------|-----|
| **Primary question** | "How was this edited?" | "Was this actually captured?" |
| **Focus** | Edit history, asset provenance | Capture moment, sequence integrity |
| **Deletion detection** | No | Yes (Completeness Invariant) |
| **External anchor** | Optional | Required (Silver+) |
| **Self-attestation** | Allowed | Mitigated by external TSA |

## Interoperability Modes

### Mode 1: CPP-Only

For CPP-aware applications only.

```
[Capture Device] → [CPP Events] → [CPP SEAL] → [Verification Pack]
```

### Mode 2: CPP + C2PA Export

CPP data embedded as C2PA assertion for broad compatibility.

```
[Capture Device] → [CPP Events] → [CPP SEAL] → [C2PA Manifest Export]
```

### Mode 3: CPP Reference in C2PA

Minimal integration—C2PA manifest references CPP verification URL.

```
C2PA Manifest
├── c2pa.captured action
└── vso.cpp.verification_url → https://verify.veritaschain.org/cpp/...
```

## Export Format

### CPP as C2PA Assertion

```json
{
  "c2pa.actions": [
    {
      "action": "c2pa.captured",
      "softwareAgent": "VeriCapture/1.0",
      "when": "2026-01-18T10:30:00.000Z",
      "parameters": {
        "vso.cpp.version": "1.0",
        "vso.cpp.verification_code": "CPP-2026-ABC123XYZ",
        "vso.cpp.verification_url": "https://verify.veritaschain.org/cpp/CPP-2026-ABC123XYZ",
        "vso.cpp.merkle_root": "sha256:1234567890abcdef...",
        "vso.cpp.completeness_valid": true,
        "vso.cpp.external_anchor_type": "RFC3161",
        "vso.cpp.tsa_url": "https://freetsa.org/tsr"
      }
    }
  ]
}
```

### Custom Assertion Label

Namespace: `vso.cpp`

| Label | Type | Description |
|-------|------|-------------|
| `vso.cpp.version` | string | CPP spec version |
| `vso.cpp.verification_code` | string | Unique verification code |
| `vso.cpp.verification_url` | uri | Permanent verification URL |
| `vso.cpp.merkle_root` | string | Merkle tree root hash |
| `vso.cpp.completeness_valid` | boolean | Completeness Invariant status |
| `vso.cpp.external_anchor_type` | string | Anchor type (RFC3161, SCITT) |
| `vso.cpp.event_count` | integer | Number of events in collection |

## Use Cases

### Enterprise Dual-System

```
┌─────────────────────────────────────────────────────────────────┐
│ INTERNAL SYSTEM (Full CPP)                                      │
│   • Complete hash chain                                         │
│   • Completeness Invariant                                      │
│   • ACE biometric attestation                                   │
│   • Full audit trail                                            │
├─────────────────────────────────────────────────────────────────┤
│ EXPORT LAYER                                                    │
│   • Generate C2PA manifest                                      │
│   • Embed CPP verification URL                                  │
│   • Maintain interoperability                                   │
├─────────────────────────────────────────────────────────────────┤
│ EXTERNAL DISTRIBUTION                                           │
│   • C2PA tools: Basic provenance                                │
│   • CPP tools: Full verification + deletion detection           │
└─────────────────────────────────────────────────────────────────┘
```

### Journalism Workflow

1. Journalist captures with CPP Gold (ACE enabled)
2. Internal review uses full CPP verification
3. Publication exports with C2PA for broad compatibility
4. Advanced readers can verify via CPP URL

## Key Differences to Highlight

### What CPP Adds Over C2PA

1. **Completeness Invariant** - Detects deleted events
2. **Mandatory External Anchor** - Prevents self-attestation abuse
3. **Privacy by Design** - Location OFF by default
4. **Clear Terminology** - "Provenance Available" not "Verified"

### What C2PA Provides

1. **Edit History** - Track modifications over time
2. **Broad Ecosystem** - Adobe, Microsoft, BBC support
3. **Asset Binding** - Link provenance to specific files

## Implementation Notes

### Hash Alignment

Both CPP and C2PA use:
- SHA-256 for content hashing
- Ed25519 supported for signatures
- JSON-based metadata

### Timestamp Compatibility

C2PA timestamps can reference the same RFC 3161 TSA as CPP external anchors, providing consistent temporal evidence.

---

**Document ID:** VSO-CPP-C2PA-001  
**Version:** 1.0  
**Date:** 2026-01-18
