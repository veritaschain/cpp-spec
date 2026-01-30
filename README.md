# Capture Provenance Profile (CPP)

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Spec Version](https://img.shields.io/badge/spec-v1.5-blue.svg)](docs/CPP-Specification-v1.5.md)
[![Part of VAP](https://img.shields.io/badge/VAP-Framework-green.svg)](https://github.com/veritaschain)

**Open specification for cryptographically verifiable media capture provenance.**

CPP proves "this media was actually captured at this moment" with deletion detection, external timestamping, and privacy-by-design. Part of the [VAP (Verifiable AI Provenance) Framework](https://github.com/veritaschain).

---

## 🎯 Why CPP?

Existing content provenance solutions face critical challenges:

| Problem | CPP Solution |
|---------|--------------|
| **Self-attestation abuse** | RFC 3161 TSA mandatory (independent third-party) |
| **Metadata stripped by platforms** | Verification URL + PHASH recovery |
| **No deletion detection** | Completeness Invariant (XOR hash sum) |
| **"Verified" misleads users** | "Provenance Available" terminology |
| **Trust list gatekeeping** | Open TSA ecosystem (free options) |
| **Exclusion list vulnerabilities** | NO exclusion lists |

## 🔑 Key Features

### 1. Completeness Invariant
Mathematically detect ANY missing events in the capture chain:
```
hash_sum = H(E₁) ⊕ H(E₂) ⊕ ... ⊕ H(Eₙ)
Delete any event → hash_sum mismatch → VIOLATION DETECTED
```

### 2. External Third-Party Verification
RFC 3161 TSA timestamps eliminate self-attestation:
```
Creator signs → TSA countersigns → INDEPENDENT VERIFICATION
```

### 3. Privacy by Design
- Location: OFF by default
- Zero-knowledge biometric attestation (ACE)
- GDPR-compliant crypto-shredding

### 4. C2PA Interoperability
Complement, not compete:
- C2PA: "How was this edited?"
- CPP: "Was this actually captured?"

---

## 📁 Repository Structure

```
cpp-spec/
├── docs/
│   └── CPP-Specification-v1.0.md
│   └── CPP-Specification-v1.1.md
│   └── CPP-Specification-v1.2.md
│   └── CPP-Specification-v1.3.md
│   └── CPP-Specification-v1.4.md    # Main specification
│   └── CPP-Specification-v1.5.md    # Main specification
├── schemas/
│   ├── cpp/                          # Core JSON schemas
│   └── ace/                          # ACE extension schemas
├── examples/
│   ├── cpp-core/                     # Core examples
│   └── cpp-ace/                      # ACE examples
├── test-vectors/                     # Conformance test data
├── regulatory-mapping/               # EU AI Act, GDPR mapping
└── tools/                            # Reference utilities
```

---

## 🚀 Quick Start

### Verification URL
Every CPP-protected capture has a permanent URL:
```
https://verify.veritaschain.org/cpp/{verification_code}
```

### Basic Event Structure
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

## 📊 Conformance Levels

| Level | Target | TSA Anchor | ACE | Use Case |
|-------|--------|------------|-----|----------|
| **Bronze** | Hobbyists | Optional | Optional | Personal photos |
| **Silver** | Families | Daily | Optional | Family memories |
| **Gold** | Legal/Journalism | Per-capture | Required | Court evidence |

---

## 🔗 Related Projects

- [VCP (VeritasChain Protocol)](https://github.com/veritaschain/vcp-spec) - Algorithmic trading
- [CAP (Creative AI Profile)](https://github.com/veritaschain/cap-spec) - AI content generation
- [VAP Framework](https://github.com/veritaschain) - Parent framework

---

## 📜 UI Guidelines

**CPP explicitly avoids "Verified" terminology:**

| ✅ Use | ❌ Avoid |
|--------|---------|
| "Provenance Available" | "Verified" |
| "Capture Recorded" | "Authenticated" |
| ℹ️ Information icon | ✓ Checkmark |

> **Required disclosure:** "This shows capture data. It does NOT verify content truthfulness or source trustworthiness."

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
