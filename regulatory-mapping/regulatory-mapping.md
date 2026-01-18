# CPP Regulatory Mapping

## Overview

This document maps CPP v1.0 features to relevant regulatory requirements.

---

## EU AI Act

### Article 50: Transparency Requirements

| Requirement | CPP Feature | Conformance Level |
|-------------|-------------|-------------------|
| AI-generated content labeling | Not applicable (CPP is for capture, not AI generation - see CAP) | N/A |
| Content provenance disclosure | Verification Pack | All levels |
| Machine-readable metadata | JSON format with schemas | All levels |

### Article 12: Record-keeping

| Requirement | CPP Feature | Conformance Level |
|-------------|-------------|-------------------|
| Logging of events | Event chain with hash linking | All levels |
| Timestamps | Device + RFC 3161 TSA | Silver+ |
| Audit trail | Merkle tree + Completeness Invariant | All levels |

---

## GDPR

### Article 17: Right to Erasure

| Requirement | CPP Feature | Notes |
|-------------|-------------|-------|
| Data deletion | Crypto-shredding (DELETE event) | Content unrecoverable |
| Proof of deletion | DELETE event in chain | Merkle proof retained |
| Audit trail | Hash retained, content destroyed | Proves deletion occurred |

### Article 25: Data Protection by Design

| Requirement | CPP Feature | Notes |
|-------------|-------------|-------|
| Privacy by default | Location OFF by default | Explicit opt-in required |
| Data minimization | Minimal metadata collected | User controls disclosure |
| Pseudonymization | Anonymous/Pseudonymous identity modes | Device-only signing supported |

### Biometric Data (Article 9)

| Requirement | ACE Feature | Notes |
|-------------|-------------|-------|
| No processing of biometric data | NO_BIOMETRIC_DATA_STORED | Only auth metadata |
| Special category protection | Zero-knowledge attestation | No identifiable data |

---

## MiFID II / RTS 25 (If CPP used for financial documentation)

| Requirement | CPP Feature | Notes |
|-------------|-------------|-------|
| Timestamp accuracy | RFC 3161 TSA | External verification |
| Record retention | Verification URL (50+ year SLA) | Permanent availability |
| Audit trail integrity | Completeness Invariant | Deletion detection |

---

## California Consumer Privacy Act (CCPA)

| Requirement | CPP Feature | Notes |
|-------------|-------------|-------|
| Right to deletion | Crypto-shredding | DELETE event |
| Right to know | Verification Pack transparency | All metadata accessible |
| Opt-out of sale | N/A (no data sale in protocol) | - |

---

## Summary by Conformance Level

### Bronze Level
- Basic GDPR compliance (privacy by design)
- Event integrity and chain linking
- Completeness Invariant

### Silver Level
- Enhanced audit trail (daily TSA)
- Better timestamp evidence
- PHASH recovery registration

### Gold Level
- Full forensic evidence grade
- Per-capture external timestamp
- Biometric attestation (ACE)
- Suitable for legal proceedings

---

## Disclaimer

This mapping is informational only. Consult legal counsel for specific compliance requirements.

---

**Document ID:** VSO-CPP-REG-001  
**Version:** 1.0  
**Date:** 2026-01-18
