# Capture Provenance Profile (CPP) Specification

**Version:** 1.5  
**Status:** Final  
**Date:** 2026-01-30  
**Document ID:** VSO-CPP-SPEC-006  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** CC BY 4.0 International

**Revision History:**
| Rev | Date | Changes |
|-----|------|---------|
| 1 | 2026-01-30 | Initial v1.5 DRAFT |
| 2 | 2026-01-30 | Design review fixes: Silent Failure enforcement, ConfidenceLevel model, Interaction scope clarification, checkmark prohibition, iOS/Android fallback requirements |
| 3 | 2026-01-30 | PROVENANCE_PARTIAL→silent passthrough統一, FakeMarkCountermeasuresスコープ明記, 200ms budget short-circuit要件追加 |
| Final | 2026-01-30 | iOS実装例を仕様意図に合わせて全面改訂（Re-share REQUIRED, URL scheme Informative分離）, 型安全なVerificationResult定義追加 |

---

## Abstract

The Capture Provenance Profile (CPP) is an open specification for cryptographically verifiable media capture provenance. Unlike edit-history approaches such as C2PA, CPP focuses on proving "this media was actually captured at this moment" with **deletion detection**, **external timestamping**, and **privacy-by-design** architecture.

CPP v1.5 introduces the **Pre-Publish Verification Extension** for verifying provenance at the moment of social media sharing, enabling users to indicate that their content has traceable origin without blocking the sharing flow or making truth claims.

---

## 1. Changes from v1.4

| Item | v1.4 | v1.5 | Rationale |
|------|------|------|-----------|
| **Pre-Publish Verification** | Not specified | NEW extension | SNS sharing workflow integration |
| **ProvenanceIndicator** | Not specified | NEW object | Visual mark specification |
| **VerificationResult** | Not specified | NEW object | Lightweight verification output |
| **ShareContext** | Not specified | NEW object | Platform-specific sharing metadata |
| **Prohibited Terms** | Not specified | 7 terms defined | Legal compliance, user protection |
| **Disclaimer Templates** | Not specified | 3 levels defined | Regulatory compliance |
| **C2PA Interoperability** | Implicit | Explicit mapping | Cross-standard compatibility |

---

## 2. Pre-Publish Verification Extension

### 2.1 Overview

The Pre-Publish Verification Extension enables verification of CPP provenance data at the moment a user shares content to social media platforms.

**Core Principles:**

| Principle | Description |
|-----------|-------------|
| **Provenance ≠ Truth** | The system proves traceable origin exists, NOT content accuracy |
| **Non-Blocking** | NEVER blocks or delays the sharing flow |
| **Silent Failure** | If verification fails, content passes through unmarked |
| **Privacy-by-Design** | All verification performed on-device, no external data transmission |
| **Platform-Agnostic** | Works without SNS platform cooperation |

**Design Philosophy:**

```
SNS投稿直前検証とは、
投稿の自由を一切妨げず、
"後から辿れる出自"だけを静かに残す仕組みである。
```

### 2.2 Verification Trigger Points

| Platform | Trigger Mechanism | Technical Implementation |
|----------|-------------------|--------------------------|
| Android | ACTION_SEND Intent | Share Target Activity |
| iOS | Share Extension | NSExtensionItem handler |
| Web | Share API | navigator.share() intercept |
| Desktop | Clipboard/Drag | System hook (platform-specific) |

### 2.3 Verification Scope

The Pre-Publish Verification performs LIGHTWEIGHT checks only:

| Check | Required | Description | Max Time |
|-------|----------|-------------|----------|
| CPP Manifest Existence | YES | Detect CPP JSON in metadata | 50ms |
| C2PA JUMBF Scan | YES | Detect JUMBF box signature | 50ms |
| Signature Validity | OPTIONAL | Verify top-level signature | 200ms |
| Certificate Chain | OPTIONAL | Validate against trust store | 100ms |
| Hash Verification | NO | Full content hash (deferred) | N/A |

**Total Budget:** 200ms (hard limit)

**CRITICAL:** There is NO soft limit with user notification. All timeouts result in silent passthrough. Internal metrics MAY be logged for debugging purposes, but MUST NOT be exposed to the user. This maintains the "Non-Blocking" and "Silent Failure" principles without exception.

**OPTIONAL checks MUST fit within the same 200ms total budget.** Implementations MUST short-circuit verification once the budget is exceeded, returning `VERIFICATION_TIMEOUT` and proceeding with silent passthrough. The individual check times listed above are maximums; implementations SHOULD parallelize where possible.

### 2.4 Verification Result

The verification result uses a **three-level confidence model** to prevent over-claiming:

| Level | Description | Available Fields |
|-------|-------------|------------------|
| `DETECTED` | Manifest structure found but not parsed | Source.Type only |
| `PARSED` | Manifest parsed, fields extracted | Source, CaptureTimestamp, Indicators (partial) |
| `VERIFIED` | Signature validated against trust store | All fields including Signer |

```json
{
  "VerificationResult": {
    "Status": "PROVENANCE_AVAILABLE",
    "ConfidenceLevel": "VERIFIED",
    "Timestamp": "2026-01-30T10:30:00.123Z",
    "Source": {
      "Type": "CPP",
      "Version": "1.4",
      "ManifestHash": "sha256:abc123..."
    },
    "Signer": {
      "Name": "VeraSnap Capture",
      "Organization": "VeritasChain Co., Ltd.",
      "CertificateIssuer": "DigiCert"
    },
    "CaptureTimestamp": "2026-01-30T10:25:00.000Z",
    "Indicators": {
      "HasExternalTimestamp": true,
      "HasBiometricBinding": true,
      "HasDepthAnalysis": true,
      "ScreenDetected": false
    },
    "VerificationDuration": 187
  }
}
```

**CRITICAL Field Visibility Rules:**

| Field | DETECTED | PARSED | VERIFIED |
|-------|:--------:|:------:|:--------:|
| Status | ✓ | ✓ | ✓ |
| ConfidenceLevel | ✓ | ✓ | ✓ |
| Timestamp | ✓ | ✓ | ✓ |
| Source.Type | ✓ | ✓ | ✓ |
| Source.Version | — | ✓ | ✓ |
| Source.ManifestHash | — | ✓ | ✓ |
| CaptureTimestamp | — | ✓ | ✓ |
| Indicators | — | Partial | ✓ |
| **Signer** | — | — | ✓ only |
| **CertificateIssuer** | — | — | ✓ only |

**Rationale:** Displaying Signer information without cryptographic verification creates a spoofing vector. Attackers could craft manifests with fake signer names that pass detection but fail verification. By restricting Signer to VERIFIED level only, we prevent this misrepresentation.

### 2.5 Status Values

| Status | Description | Action |
|--------|-------------|--------|
| `PROVENANCE_AVAILABLE` | Valid CPP/C2PA manifest found and VERIFIED | Apply indicator |
| `PROVENANCE_PARTIAL` | Manifest found but verification incomplete | Silent passthrough (no mark)* |
| `PROVENANCE_UNAVAILABLE` | No manifest or verification failed | Silent passthrough |
| `VERIFICATION_TIMEOUT` | Verification exceeded time budget | Silent passthrough |
| `VERIFICATION_ERROR` | Technical error during verification | Silent passthrough |

*`PROVENANCE_PARTIAL` MAY be surfaced in VeraSnap app preview or verification web page (L2 panel), but MUST NOT apply any indicator to the shared content. This maintains Non-Blocking and Silent Failure principles.

---

## 3. Provenance Indicator Specification

### 3.1 Indicator Types

CPP v1.5 defines three types of provenance indicators:

| Type | Visibility | Survival Rate | Use Case |
|------|------------|---------------|----------|
| **VisualMark** | Visible | High | Primary indicator |
| **DynamicQR** | Visible | High | Verification URL |
| **InvisibleWatermark** | Invisible | Medium-High | Backup/forensic |

### 3.2 VisualMark Specification

**IMPORTANT:** VisualMark is a **purely visual, non-interactive** element once composited into the image. The mark becomes pixels in the image and CANNOT respond to taps or interactions on social media platforms.

```json
{
  "ProvenanceIndicator": {
    "Type": "VisualMark",
    "Position": "BottomRight",
    "Size": {
      "Width": 48,
      "Height": 48,
      "Unit": "dp"
    },
    "Margin": {
      "Right": 8,
      "Bottom": 8,
      "Unit": "dp"
    },
    "Opacity": 0.85,
    "Background": {
      "Color": "#000000",
      "Opacity": 0.6,
      "CornerRadius": 8
    },
    "Icon": {
      "Type": "ProvenanceAvailable",
      "Color": "#FFFFFF",
      "Style": "InfoCircle"
    }
  }
}
```

**Icon Style Constraints:**

| Allowed | Prohibited | Rationale |
|---------|------------|-----------|
| ℹ️ Info circle | ✓ Checkmark | Checkmarks imply verification/approval |
| 🔗 Link/chain | ✅ Green check | Green checks imply "correct" or "safe" |
| 📋 Document | 🛡️ Shield | Shields imply security guarantee |
| 🏷️ Tag/label | ⭐ Star | Stars imply rating or endorsement |

**Interaction Scope:**

| Context | Interactive? | Notes |
|---------|:------------:|-------|
| SNS post (after share) | ❌ NO | Pixels only, no tap response |
| VeraSnap preview (before share) | ✓ YES | App can show L2/L3 panels |
| Verification web page | ✓ YES | Full L2/L3 experience |

L2/L3 information panels are provided ONLY through:
1. The verification URL encoded in the DynamicQR
2. VeraSnap app's internal preview before sharing

### 3.3 Position Options

| Position | Priority | Rationale |
|----------|----------|-----------|
| `BottomRight` | 1 (Default) | Least intrusive, standard placement |
| `BottomLeft` | 2 | Alternative if right is occupied |
| `TopRight` | 3 | Fallback position |
| `TopLeft` | 4 | Last resort |
| `Diagonal` | Special | Multiple positions for crop resistance |

### 3.4 DynamicQR Specification

```json
{
  "ProvenanceIndicator": {
    "Type": "DynamicQR",
    "Position": "BottomLeft",
    "Size": {
      "Width": 64,
      "Height": 64,
      "Unit": "dp"
    },
    "Content": {
      "URL": "https://verify.veritaschain.org/v/{proof_id}",
      "Parameters": {
        "proof_id": "evt_abc123def456",
        "asset_hash": "sha256:789xyz...",
        "timestamp": "1706612400"
      }
    },
    "ErrorCorrection": "M",
    "QuietZone": 2
  }
}
```

### 3.5 InvisibleWatermark Specification

```json
{
  "ProvenanceIndicator": {
    "Type": "InvisibleWatermark",
    "Method": "DCT",
    "Payload": {
      "Format": "CPP_WATERMARK_V1",
      "Fields": ["proof_id", "timestamp", "signature_fragment"],
      "MaxBytes": 128
    },
    "Robustness": {
      "JPEGQuality": 50,
      "Resize": 0.5,
      "Crop": 0.1
    },
    "Detection": {
      "Algorithm": "DCT_CORRELATION",
      "Threshold": 0.7
    }
  }
}
```

### 3.6 C2PA Soft Binding Compatibility

For C2PA-compatible implementations, the InvisibleWatermark MAY use C2PA Soft Binding:

```json
{
  "ProvenanceIndicator": {
    "Type": "InvisibleWatermark",
    "Method": "C2PA_SOFT_BINDING",
    "Reference": "https://spec.c2pa.org/specifications/specifications/2.2/softbinding/",
    "Payload": {
      "ManifestHash": "sha256:...",
      "C2PAVersion": "2.2"
    }
  }
}
```

---

## 4. Platform Implementation

### 4.1 Android Implementation

#### 4.1.1 Architecture: Intent Proxy Model

```
┌─────────────────────────────────────────────────────────┐
│  Source App (Gallery, Camera, etc.)                      │
│  └─ User taps "Share"                                    │
└─────────────────────┬───────────────────────────────────┘
                      │ ACTION_SEND Intent
                      ▼
┌─────────────────────────────────────────────────────────┐
│  VeraSnap Share Target Activity                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │  1. Receive Intent (image/*, video/*)               ││
│  │  2. Extract media URI                                ││
│  │  3. Perform lightweight verification (200ms)         ││
│  │  4. Compose indicator (if PROVENANCE_AVAILABLE)      ││
│  │  5. Save to cache with FileProvider URI              ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────┬───────────────────────────────────┘
                      │ Explicit Intent (setPackage)
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Target SNS App (Instagram, X, etc.)                     │
│  └─ Receives processed media                             │
└─────────────────────────────────────────────────────────┘
```

#### 4.1.2 AndroidManifest.xml

```xml
<activity
    android:name=".share.ProvenanceShareActivity"
    android:exported="true"
    android:theme="@style/Theme.Transparent">
    
    <intent-filter>
        <action android:name="android.intent.action.SEND" />
        <category android:name="android.intent.category.DEFAULT" />
        <data android:mimeType="image/*" />
    </intent-filter>
    
    <intent-filter>
        <action android:name="android.intent.action.SEND" />
        <category android:name="android.intent.category.DEFAULT" />
        <data android:mimeType="video/*" />
    </intent-filter>
    
    <meta-data
        android:name="android.service.chooser.chooser_target_service"
        android:value=".share.ProvenanceChooserTargetService" />
</activity>

<provider
    android:name="androidx.core.content.FileProvider"
    android:authorities="${applicationId}.fileprovider"
    android:exported="false"
    android:grantUriPermissions="true">
    <meta-data
        android:name="android.support.FILE_PROVIDER_PATHS"
        android:resource="@xml/file_paths" />
</provider>
```

#### 4.1.3 Kotlin Implementation

```kotlin
class ProvenanceShareActivity : AppCompatActivity() {
    
    private val verifier = CPPVerifier()
    private val compositor = IndicatorCompositor()
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        when (intent?.action) {
            Intent.ACTION_SEND -> handleSendIntent(intent)
            else -> finish()
        }
    }
    
    private fun handleSendIntent(intent: Intent) {
        val mediaUri = intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM) ?: run {
            forwardToTarget(intent)
            return
        }
        
        lifecycleScope.launch {
            val result = withTimeoutOrNull(200) {
                verifier.verify(mediaUri)
            } ?: VerificationResult.Timeout
            
            when (result.status) {
                Status.PROVENANCE_AVAILABLE -> {
                    val processedUri = compositor.compose(mediaUri, result)
                    forwardToTarget(intent, processedUri)
                }
                else -> {
                    // Silent passthrough
                    forwardToTarget(intent)
                }
            }
        }
    }
    
    private fun forwardToTarget(intent: Intent, processedUri: Uri? = null) {
        val targetPackage = intent.getStringExtra(EXTRA_TARGET_PACKAGE)
        
        val forwardIntent = Intent(Intent.ACTION_SEND).apply {
            type = intent.type
            putExtra(Intent.EXTRA_STREAM, processedUri ?: intent.getParcelableExtra(Intent.EXTRA_STREAM))
            targetPackage?.let { setPackage(it) }
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        
        // CRITICAL: setPackage may fail if target app is not installed
        // MUST fall back to chooser in that case
        try {
            if (targetPackage != null && 
                packageManager.resolveActivity(forwardIntent, 0) != null) {
                startActivity(forwardIntent)
            } else {
                // Fallback to chooser (REQUIRED)
                startActivity(Intent.createChooser(forwardIntent, null))
            }
        } catch (e: ActivityNotFoundException) {
            // Fallback to chooser on any failure (REQUIRED)
            startActivity(Intent.createChooser(forwardIntent, null))
        }
        
        finish()
    }
}
```

### 4.2 iOS Implementation

**CRITICAL CONSTRAINTS:**
- iOS Share Extensions CANNOT directly launch other apps
- Direct URL schemes are LIMITED and unreliable
- **DEFAULT behavior MUST be Re-present Share Sheet**
- Direct URL schemes MAY be attempted as optimization only

#### 4.2.1 Architecture: Share Extension with Re-Share

```
┌─────────────────────────────────────────────────────────┐
│  Source App (Photos, Camera, etc.)                       │
│  └─ User taps "Share"                                    │
└─────────────────────┬───────────────────────────────────┘
                      │ NSExtensionItem
                      ▼
┌─────────────────────────────────────────────────────────┐
│  VeraSnap Share Extension (120MB limit)                  │
│  ┌─────────────────────────────────────────────────────┐│
│  │  1. Receive attachments via NSItemProvider          ││
│  │  2. Downsample if needed (memory optimization)       ││
│  │  3. Perform lightweight verification (200ms)         ││
│  │  4. Compose indicator (if PROVENANCE_AVAILABLE)      ││
│  │  5. Save to App Group shared container               ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────┬───────────────────────────────────┘
                      │ 
                      ▼
┌─────────────────────────────────────────────────────────┐
│  DEFAULT: Re-present Share Sheet (REQUIRED)              │
│  UIActivityViewController with processed image           │
│  - Works with ALL apps                                   │
│  - Two-step UX but reliable                              │
├─────────────────────────────────────────────────────────┤
│  OPTIONAL (MAY): Direct URL Scheme                       │
│  - Limited to apps with documented schemes               │
│  - Instagram: library only, no direct post               │
│  - MUST fall back to Re-share if canOpenURL fails        │
└─────────────────────────────────────────────────────────┘
```

#### 4.2.2 Info.plist Configuration

```xml
<key>NSExtension</key>
<dict>
    <key>NSExtensionAttributes</key>
    <dict>
        <key>NSExtensionActivationRule</key>
        <dict>
            <key>NSExtensionActivationSupportsImageWithMaxCount</key>
            <integer>1</integer>
            <key>NSExtensionActivationSupportsMovieWithMaxCount</key>
            <integer>1</integer>
        </dict>
    </dict>
    <key>NSExtensionMainStoryboard</key>
    <string>ShareViewController</string>
    <key>NSExtensionPointIdentifier</key>
    <string>com.apple.share-services</string>
</dict>

<key>LSApplicationQueriesSchemes</key>
<array>
    <string>instagram</string>
    <string>twitter</string>
    <string>fb</string>
    <string>tiktok</string>
</array>
```

#### 4.2.3 Swift Implementation (Normative)

The following implementation demonstrates the REQUIRED re-share pattern:

```swift
import UIKit
import UniformTypeIdentifiers

class ShareViewController: UIViewController {
    
    private let verifier = CPPVerifier()
    private let compositor = IndicatorCompositor()
    private var processedImage: UIImage?
    private var originalImage: UIImage?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        processAttachments()
    }
    
    private func processAttachments() {
        guard let extensionItem = extensionContext?.inputItems.first as? NSExtensionItem,
              let attachments = extensionItem.attachments else {
            completeWithError()
            return
        }
        
        for provider in attachments {
            if provider.hasItemConformingToTypeIdentifier(UTType.image.identifier) {
                processImage(provider: provider)
                return
            }
        }
        
        completeWithError()
    }
    
    private func processImage(provider: NSItemProvider) {
        provider.loadItem(forTypeIdentifier: UTType.image.identifier, options: nil) { [weak self] item, error in
            guard let self = self, error == nil else {
                self?.completeWithError()
                return
            }
            
            let image: UIImage?
            if let url = item as? URL, let data = try? Data(contentsOf: url) {
                image = UIImage(data: data)
            } else if let img = item as? UIImage {
                image = img
            } else if let data = item as? Data {
                image = UIImage(data: data)
            } else {
                self.completeWithError()
                return
            }
            
            guard let inputImage = image else {
                self.completeWithError()
                return
            }
            
            self.originalImage = inputImage
            
            // Verification with 200ms hard limit
            let result = self.verifyWithTimeout(image: inputImage, timeout: 0.2)
            
            switch result.status {
            case .provenanceAvailable:
                // Apply indicator only for VERIFIED provenance
                if result.confidenceLevel == .verified {
                    self.processedImage = self.compositor.compose(
                        image: inputImage, 
                        result: result
                    )
                } else {
                    // PARTIAL/DETECTED: silent passthrough (no mark)
                    self.processedImage = inputImage
                }
            default:
                // Silent passthrough for all other cases
                self.processedImage = inputImage
            }
            
            DispatchQueue.main.async {
                self.presentShareSheet()
            }
        }
    }
    
    private func verifyWithTimeout(image: UIImage, timeout: TimeInterval) -> VerificationResult {
        let semaphore = DispatchSemaphore(value: 0)
        var result = VerificationResult(
            status: .verificationTimeout,
            confidenceLevel: .none,
            timestamp: Date()
        )
        
        DispatchQueue.global(qos: .userInitiated).async {
            result = self.verifier.verify(image: image)
            semaphore.signal()
        }
        
        let waitResult = semaphore.wait(timeout: .now() + timeout)
        if waitResult == .timedOut {
            // CRITICAL: Return timeout status, proceed with silent passthrough
            return VerificationResult(
                status: .verificationTimeout,
                confidenceLevel: .none,
                timestamp: Date()
            )
        }
        return result
    }
    
    // REQUIRED: Always use UIActivityViewController for re-share
    private func presentShareSheet() {
        guard let image = processedImage else {
            completeWithError()
            return
        }
        
        let activityVC = UIActivityViewController(
            activityItems: [image],
            applicationActivities: nil
        )
        
        // iPad support
        if let popover = activityVC.popoverPresentationController {
            popover.sourceView = self.view
            popover.sourceRect = CGRect(x: view.bounds.midX, y: view.bounds.midY, width: 0, height: 0)
            popover.permittedArrowDirections = []
        }
        
        activityVC.completionWithItemsHandler = { [weak self] _, completed, _, _ in
            self?.extensionContext?.completeRequest(
                returningItems: nil,
                completionHandler: nil
            )
        }
        
        present(activityVC, animated: true)
    }
    
    private func completeWithError() {
        extensionContext?.cancelRequest(withError: NSError(
            domain: "org.veritaschain.verasnap.share",
            code: -1,
            userInfo: nil
        ))
    }
}

// MARK: - Supporting Types

struct VerificationResult {
    enum Status {
        case provenanceAvailable
        case provenancePartial
        case provenanceUnavailable
        case verificationTimeout
        case verificationError
    }
    
    enum ConfidenceLevel {
        case none
        case detected
        case parsed
        case verified
    }
    
    let status: Status
    let confidenceLevel: ConfidenceLevel
    let timestamp: Date
    var signer: Signer?  // Only populated when confidenceLevel == .verified
    
    struct Signer {
        let name: String
        let organization: String
        let certificateIssuer: String
    }
}
```

#### 4.2.4 Direct URL Scheme (Informative, MAY)

The following pattern is OPTIONAL and MAY be attempted as an optimization. However, implementations MUST fall back to the re-share pattern (4.2.3) when URL schemes fail or are unavailable.

**WARNING:** Share Extensions have significant limitations:
- `UIApplication.shared` is NOT directly accessible
- URL scheme availability varies by iOS version and target app
- Many apps do not support URL scheme-based media sharing

```swift
// INFORMATIVE ONLY - Not recommended for production
// This demonstrates the MAY optimization, not the REQUIRED flow

extension ShareViewController {
    
    /// Attempt direct URL scheme as optimization (MAY)
    /// MUST fall back to presentShareSheet() on ANY failure
    private func attemptDirectShare(image: UIImage) {
        // Save to shared container first
        guard let imageURL = saveToSharedContainer(image) else {
            presentShareSheet()  // REQUIRED fallback
            return
        }
        
        // Attempt URL scheme (unreliable in extensions)
        // Most Share Extensions cannot reliably use this pattern
        // Fall back to re-share is REQUIRED
        presentShareSheet()
    }
    
    private func saveToSharedContainer(_ image: UIImage) -> URL? {
        guard let data = image.jpegData(compressionQuality: 0.9),
              let containerURL = FileManager.default.containerURL(
                  forSecurityApplicationGroupIdentifier: "group.org.veritaschain.verasnap"
              ) else {
            return nil
        }
        
        let fileURL = containerURL.appendingPathComponent(UUID().uuidString + ".jpg")
        do {
            try data.write(to: fileURL)
            return fileURL
        } catch {
            return nil
        }
    }
}
```

**Implementation Guidance:**
- The re-share pattern (4.2.3) is the ONLY reliable method in iOS Share Extensions
- Direct URL schemes are documented for completeness but NOT recommended
- If URL scheme optimization is attempted, failure MUST result in re-share fallback
- Never assume `UIApplication.shared` is available in extension context

### 4.3 Memory Optimization (iOS)

iOS Share Extensions have a strict **120MB memory limit**. Implementations MUST:

```swift
// 1. Use CGImageSource for memory-efficient loading
func loadImageEfficiently(url: URL) -> CGImage? {
    let options: [CFString: Any] = [
        kCGImageSourceShouldCache: false,
        kCGImageSourceCreateThumbnailFromImageAlways: true,
        kCGImageSourceThumbnailMaxPixelSize: 2048,
        kCGImageSourceCreateThumbnailWithTransform: true
    ]
    
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
        return nil
    }
    
    return CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary)
}

// 2. Use memory-mapped files for large content
func loadDataEfficiently(url: URL) -> Data? {
    return try? Data(contentsOf: url, options: .mappedIfSafe)
}

// 3. Process in tiles for very large images
func processInTiles(image: CGImage, tileSize: Int = 512) {
    // Implementation for tile-based processing
}
```

---

## 5. Security Considerations

### 5.1 STRIDE Threat Analysis

| Threat | Category | Likelihood | Severity | Mitigation |
|--------|----------|------------|----------|------------|
| **Fake Mark Display** | Spoofing | High | Medium | UI overlay, interaction detection |
| **User Misinterpretation** | Spoofing | Medium | High | Prohibited terms, disclaimers |
| **Manifest Tampering** | Tampering | Medium | High | Cryptographic signatures |
| **Metadata Stripping** | Tampering | High | Low | Visual mark, invisible watermark |
| **Key Theft** | Tampering | Low | Critical | HSM, key rotation, revocation |
| **Audit Denial** | Repudiation | Medium | Medium | SCITT integration (future) |
| **Privacy Leakage** | Info Disclosure | Medium | Medium | On-device verification only |
| **Verification DoS** | DoS | Low | Medium | Timeout, resource limits |
| **Certificate Collision** | Privilege Escalation | Low | Medium | Trust store management |

### 5.2 Fake Mark Countermeasures

**SCOPE:** These countermeasures apply ONLY in:
1. VeraSnap app preview UI (before sharing)
2. Verification web pages (accessed via QR code URL)

They do NOT apply to composited images shared on SNS platforms, where the VisualMark is purely visual (pixels) and cannot respond to interactions.

#### 5.2.1 UI Overlay Strategy

```json
{
  "FakeMarkCountermeasures": {
    "OverlayPosition": {
      "Strategy": "SlightOverlap",
      "Description": "Mark slightly overlaps content edge",
      "Rationale": "Static fake icons cannot replicate exact positioning"
    },
    "InteractionBehavior": {
      "OnTap": "ShowL2Panel",
      "OnLongPress": "ShowL3Detail",
      "OnHover": "IncreaseOpacity",
      "Rationale": "Fake static icons cannot respond to interactions"
    },
    "DynamicElements": {
      "AnimatedBorder": true,
      "PulseOnFirstView": true,
      "Rationale": "Static images cannot replicate animations"
    }
  }
}
```

#### 5.2.2 QR Code Verification

```json
{
  "QRVerification": {
    "URL": "https://verify.veritaschain.org/v/{proof_id}",
    "Payload": {
      "proof_id": "Unique identifier",
      "asset_hash": "SHA-256 of original content",
      "timestamp": "Unix timestamp of composition",
      "signature": "ECDSA signature of payload"
    },
    "ServerValidation": {
      "HashComparison": "Upload image, compare hash",
      "TimestampValidation": "Check against original capture time",
      "SignatureVerification": "Verify against known public key"
    }
  }
}
```

### 5.3 Trust Store Management

```json
{
  "TrustStore": {
    "RootCertificates": {
      "UpdateMethod": "App update or background fetch",
      "SignatureVerification": "Required for all updates",
      "FallbackBehavior": "Use bundled certificates"
    },
    "RevocationList": {
      "UpdateFrequency": "Daily background check",
      "EmergencyRevocation": "Push notification trigger",
      "OfflineBehavior": "Use cached list up to 7 days"
    },
    "CertificateTransparency": {
      "Enabled": true,
      "LogServers": ["Google Argon", "DigiCert Yeti"],
      "SCTValidation": "Required for high-assurance verification"
    }
  }
}
```

---

## 6. Legal Compliance

### 6.1 Prohibited Terms

The following terms MUST NOT be used in UI, documentation, or marketing:

| Prohibited Term | Reason | Risk |
|-----------------|--------|------|
| `Verified` | Implies platform endorsement | Platform TOS violation, user confusion |
| `Authentic` | Implies truth verification | False advertising, legal liability |
| `Official` | Implies authority endorsement | Trademark issues, user confusion |
| `Guaranteed` | Implies warranty | Consumer protection law violation |
| `Safe` / `Trusted` | Implies security assessment | Liability for harmful content |
| `Checked` / `Reviewed` | Implies content moderation | Liability for content |
| `Real` / `True` | Implies truth verification | Defamation risk, legal liability |

### 6.2 Recommended Terms

| Term (English) | Term (Japanese) | Description |
|----------------|-----------------|-------------|
| `Provenance Available` | `出所情報あり` | Neutral, factual |
| `Content Credentials` | `コンテンツ認証情報` | C2PA standard term |
| `Source Information` | `ソース情報` | Descriptive |
| `Origin Data` | `出自データ` | Technical term |
| `Traceable` | `追跡可能` | Factual capability |

### 6.3 Disclaimer Templates

#### 6.3.1 L1 Tooltip (Minimal)

```
EN: "Source information provided"
JA: "出所情報を提供している投稿です"
```

#### 6.3.2 L2 Panel (Standard)

```
EN: "This mark indicates that source information is available for this 
content. It does not guarantee the accuracy or truthfulness of the content."

JA: "このマークは、このコンテンツに出所情報が存在することを示します。
内容の正確性や真偽を保証するものではありません。"
```

#### 6.3.3 L3 Detail Page (Full)

```
EN:
"IMPORTANT NOTICE:
• This mark indicates that provenance data exists for this content.
• It does NOT verify the accuracy, truthfulness, or safety of the content.
• It does NOT represent endorsement by the platform operator.
• It is NOT related to advertising disclosure requirements.
• It is NOT related to AI-generated content disclosure requirements.
• Provenance verification is performed entirely on your device.
• No content data is transmitted to external servers for verification.

For more information, visit: https://veritaschain.org/provenance-faq"

JA:
"重要なお知らせ：
• このマークは、このコンテンツに出自データが存在することを示します。
• 内容の正確性、真偽、安全性を保証するものではありません。
• プラットフォーム運営者による承認を示すものではありません。
• 広告表示義務（PR表記）とは関係ありません。
• AI生成コンテンツの表示義務とは関係ありません。
• 出自検証はお使いのデバイス上で完結します。
• 検証のためにコンテンツデータが外部サーバーに送信されることはありません。

詳細情報: https://veritaschain.org/provenance-faq"
```

### 6.4 Regulatory Compliance Matrix

| Regulation | Requirement | CPP v1.5 Compliance |
|------------|-------------|---------------------|
| **EU AI Act (Art. 50)** | AI content marking | Complementary (not replacement) |
| **EU GDPR** | Data minimization | On-device processing, no transmission |
| **EU DSA** | Content transparency | Does not block content |
| **California AB 853** | Provenance disclosure | Compatible, can fulfill requirement |
| **China AI Labeling** | Explicit + implicit labels | Supports both visual and invisible marks |
| **Japan景品表示法** | No false endorsement | Prohibited terms list enforced |
| **FTC Guidelines** | No deceptive practices | Clear disclaimers required |

---

## 7. User Experience Guidelines

### 7.1 Information Disclosure Levels

Following C2PA UX recommendations, CPP v1.5 defines three information levels:

**IMPORTANT:** The L1→L2→L3 interaction flow applies ONLY within:
1. VeraSnap app's preview (before sharing)
2. Verification web page (via QR code URL)

Once composited and shared to SNS, the VisualMark is purely visual (pixels) and CANNOT respond to taps.

```
┌─────────────────────────────────────────────────────────┐
│  L1: Indicator (Always Visible)                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │  Small icon overlay on content                       ││
│  │  Position: Bottom-right corner                       ││
│  │  Size: 48x48 dp                                      ││
│  │  Interaction: ONLY in app preview or web page        ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
                      │ Tap
                      ▼
┌─────────────────────────────────────────────────────────┐
│  L2: Summary Panel (On Interaction)                      │
│  ┌─────────────────────────────────────────────────────┐│
│  │  Signer: "VeraSnap Capture"                         ││
│  │  Organization: "VeritasChain Co., Ltd."             ││
│  │  Capture Time: "2026-01-30 10:25 JST"               ││
│  │  Tool: "VeraSnap iOS 1.2.0"                         ││
│  │                                                      ││
│  │  [View Details] [Dismiss]                           ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
                      │ View Details
                      ▼
┌─────────────────────────────────────────────────────────┐
│  L3: Detail Page (Full Information)                      │
│  ┌─────────────────────────────────────────────────────┐│
│  │  === Content Information ===                        ││
│  │  Thumbnail: [Image Preview]                         ││
│  │  Hash: sha256:abc123...                             ││
│  │                                                      ││
│  │  === Provenance Chain ===                           ││
│  │  1. Capture: 2026-01-30 10:25:00 JST                ││
│  │     Device: iPhone 15 Pro                           ││
│  │     App: VeraSnap 1.2.0                             ││
│  │     TSA: rfc3161.ai.moda                            ││
│  │                                                      ││
│  │  === Verification Details ===                       ││
│  │  Signature: Valid (ECDSA P-256)                     ││
│  │  Certificate: DigiCert Code Signing                 ││
│  │  Timestamp: RFC 3161 verified                       ││
│  │  Depth Analysis: Real scene (95% confidence)        ││
│  │                                                      ││
│  │  === Disclaimer ===                                 ││
│  │  [Full disclaimer text]                             ││
│  │                                                      ││
│  │  [Verify on Web] [Export Data] [Close]              ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 7.2 Non-Intrusive Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Minimal Footprint** | Icon only, no text in L1 |
| **Fade Behavior** | Fade out after 3 seconds on video playback |
| **User Control** | Setting to disable indicator display |
| **Accessibility** | ALT text, screen reader support |
| **Contrast** | WCAG AA compliance |
| **Localization** | 10-language support minimum |

### 7.3 Silent Failure Policy

When verification fails or times out, the system MUST:

1. **NOT** display any warning or error message
2. **NOT** delay the sharing flow
3. **NOT** log the failure to user-visible locations
4. Optionally log to developer analytics (anonymized)
5. Pass the original content through unchanged

```swift
enum VerificationBehavior {
    case success(VerificationResult)
    case silentPassthrough  // All failure cases
}

func handleVerificationResult(_ result: VerificationResult) -> VerificationBehavior {
    switch result.status {
    case .provenanceAvailable:
        return .success(result)
    case .provenancePartial, .provenanceUnavailable, 
         .verificationTimeout, .verificationError:
        return .silentPassthrough
    }
}
```

---

## 8. C2PA Interoperability

### 8.1 Manifest Detection

CPP v1.5 implementations MUST support detection of both CPP and C2PA manifests:

```swift
enum ManifestType {
    case cpp(version: String)
    case c2pa(version: String)
    case both(cpp: String, c2pa: String)
    case none
}

func detectManifest(data: Data) -> ManifestType {
    let hasCPP = detectCPPManifest(data)
    let hasC2PA = detectC2PAManifest(data)
    
    switch (hasCPP, hasC2PA) {
    case (.some(let cppVer), .some(let c2paVer)):
        return .both(cpp: cppVer, c2pa: c2paVer)
    case (.some(let cppVer), .none):
        return .cpp(version: cppVer)
    case (.none, .some(let c2paVer)):
        return .c2pa(version: c2paVer)
    case (.none, .none):
        return .none
    }
}

func detectC2PAManifest(data: Data) -> String? {
    // Scan for JUMBF box with "c2pa" signature
    // JUMBF signature: 0x6A756D62 ("jumb")
    // C2PA label: "c2pa"
    let jumbfSignature: [UInt8] = [0x6A, 0x75, 0x6D, 0x62]
    // Implementation...
}
```

### 8.2 Field Mapping

| CPP Field | C2PA Equivalent | Notes |
|-----------|-----------------|-------|
| `DeviceInfo.Manufacturer` | `claim_generator` | Partial mapping |
| `DeviceInfo.Model` | `claim_generator` | Partial mapping |
| `CaptureTimestamp` | `dc:created` | ISO 8601 format |
| `SensorData.GPS` | `Exif:GPS*` | Standard EXIF mapping |
| `ProofBundle.TSA` | `c2pa.time_stamp` | RFC 3161 compatible |
| `DepthAnalysis` | No equivalent | CPP-specific extension |
| `BiometricBinding` | No equivalent | CPP-specific extension |

### 8.3 Dual-Standard Output

Implementations MAY generate both CPP and C2PA manifests:

```json
{
  "DualStandardOutput": {
    "CPP": {
      "Version": "1.5",
      "ManifestLocation": "Exif:UserComment or XMP:CPP"
    },
    "C2PA": {
      "Version": "2.1",
      "ManifestLocation": "JUMBF box"
    },
    "Synchronization": {
      "SharedFields": ["Timestamp", "GPS", "DeviceInfo"],
      "CPPOnly": ["DepthAnalysis", "BiometricBinding", "TSA"],
      "C2PAOnly": ["EditHistory", "Ingredients"]
    }
  }
}
```

---

## 9. SCITT Integration (Future)

### 9.1 Transparency Log Anchoring

Future versions MAY support SCITT (Supply Chain Integrity, Transparency, and Trust) integration:

```json
{
  "SCITTIntegration": {
    "Status": "RESERVED_FOR_FUTURE",
    "PlannedVersion": "1.6",
    "Functionality": {
      "LogAnchoring": "Record signature hash in transparency log",
      "ReceiptVerification": "Verify SCITT receipt in manifest",
      "NonRepudiation": "Prevent backdating and deletion denial"
    },
    "DesignConsiderations": {
      "Privacy": "Only hash values logged, not content",
      "Latency": "Async anchoring, not blocking",
      "Fallback": "Function without SCITT if unavailable"
    }
  }
}
```

### 9.2 Receipt Verification

```json
{
  "SCITTReceipt": {
    "LogID": "urn:ietf:scitt:log:example",
    "EntryID": "12345",
    "Timestamp": "2026-01-30T10:30:00Z",
    "InclusionProof": {
      "TreeSize": 1000000,
      "LeafIndex": 12345,
      "Hashes": ["sha256:...", "sha256:..."]
    }
  }
}
```

---

## 10. Verification Page API

### 10.1 Endpoint Specification

```yaml
openapi: 3.0.0
info:
  title: CPP Verification API
  version: 1.5.0

paths:
  /v/{proof_id}:
    get:
      summary: Get verification page for proof
      parameters:
        - name: proof_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Verification page HTML
          content:
            text/html:
              schema:
                type: string
        '404':
          description: Proof not found
    
  /api/v1/verify:
    post:
      summary: Verify uploaded content
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                proof_id:
                  type: string
      responses:
        '200':
          description: Verification result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VerificationResult'

components:
  schemas:
    VerificationResult:
      type: object
      properties:
        status:
          type: string
          enum: [MATCH, MISMATCH, PROOF_NOT_FOUND, INVALID_FORMAT]
        originalHash:
          type: string
        uploadedHash:
          type: string
        captureTimestamp:
          type: string
          format: date-time
        signer:
          type: object
          properties:
            name:
              type: string
            organization:
              type: string
```

### 10.2 Verification Page UI

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Content Verification - VeraSnap</title>
</head>
<body>
    <main>
        <h1>Content Provenance Verification</h1>
        
        <section id="summary">
            <h2>Verification Result</h2>
            <div class="status status-available">
                ℹ Provenance Available
            </div>
            <p class="status-note">Source information exists for this content</p>
        </section>
        
        <section id="details">
            <h2>Provenance Details</h2>
            <dl>
                <dt>Signer</dt>
                <dd>VeraSnap Capture</dd>
                
                <dt>Organization</dt>
                <dd>VeritasChain Co., Ltd.</dd>
                
                <dt>Capture Time</dt>
                <dd>2026-01-30 10:25:00 JST</dd>
                
                <dt>Device</dt>
                <dd>iPhone 15 Pro</dd>
                
                <dt>Timestamp Authority</dt>
                <dd>rfc3161.ai.moda (RFC 3161)</dd>
            </dl>
        </section>
        
        <section id="verify-upload">
            <h2>Verify Your Copy</h2>
            <p>Upload the image to verify it matches the original:</p>
            <form id="verify-form" enctype="multipart/form-data">
                <input type="file" name="file" accept="image/*">
                <button type="submit">Verify</button>
            </form>
            <div id="verify-result"></div>
        </section>
        
        <section id="disclaimer">
            <h2>Important Notice</h2>
            <p>This verification confirms that provenance data exists for 
               this content. It does NOT verify the accuracy or truthfulness 
               of the content itself.</p>
        </section>
    </main>
</body>
</html>
```

---

## 11. Complete Example

### 11.1 Full Pre-Publish Verification Flow

```json
{
  "CPPVersion": "1.5",
  "EventType": "PRE_PUBLISH_VERIFICATION",
  "VerificationContext": {
    "Trigger": "SHARE_EXTENSION",
    "Platform": "iOS",
    "TargetApp": "com.instagram.android",
    "Timestamp": "2026-01-30T10:30:00.123Z"
  },
  "OriginalCapture": {
    "CPPVersion": "1.4",
    "EventType": "PHOTO_CAPTURE",
    "EventID": "evt_abc123def456",
    "DeviceInfo": {
      "Manufacturer": "Apple",
      "Model": "iPhone 15 Pro",
      "DeviceClass": "Smartphone",
      "OSVersion": "iOS 18.2"
    },
    "CaptureTimestamp": "2026-01-30T10:25:00.000Z",
    "SensorData": {
      "GPS": {
        "Latitude": 35.6812,
        "Longitude": 139.7671,
        "Accuracy": 5.0
      },
      "DepthAnalysis": {
        "Available": true,
        "SensorType": "LiDAR",
        "ScreenDetection": {
          "IsLikelyScreen": false,
          "Confidence": 0.95
        }
      }
    },
    "BiometricBinding": {
      "Method": "FACE_ID",
      "Verified": true
    },
    "ProofBundle": {
      "TSAResponse": "base64:..."
    }
  },
  "VerificationResult": {
    "Status": "PROVENANCE_AVAILABLE",
    "Timestamp": "2026-01-30T10:30:00.187Z",
    "Source": {
      "Type": "CPP",
      "Version": "1.4"
    },
    "Signer": {
      "Name": "VeraSnap Capture",
      "Organization": "VeritasChain Co., Ltd."
    },
    "Indicators": {
      "HasExternalTimestamp": true,
      "HasBiometricBinding": true,
      "HasDepthAnalysis": true,
      "ScreenDetected": false
    },
    "VerificationDuration": 187
  },
  "ProvenanceIndicator": {
    "Applied": true,
    "Types": ["VisualMark", "DynamicQR", "InvisibleWatermark"],
    "VisualMark": {
      "Position": "BottomRight",
      "Size": {"Width": 48, "Height": 48}
    },
    "DynamicQR": {
      "URL": "https://verify.veritaschain.org/v/evt_abc123def456"
    },
    "InvisibleWatermark": {
      "Method": "DCT",
      "PayloadHash": "sha256:..."
    }
  },
  "ShareContext": {
    "SourceApp": "com.apple.mobileslideshow",
    "TargetApp": "com.instagram.android",
    "ShareMethod": "EXPLICIT_INTENT",
    "ProcessedMediaURI": "file:///..."
  }
}
```

---

## Appendix A: Localization Requirements

### A.1 Required Languages

| Language | Code | Priority |
|----------|------|----------|
| English | `en` | 1 (Base) |
| Japanese | `ja` | 1 |
| Chinese (Simplified) | `zh-Hans` | 2 |
| Chinese (Traditional) | `zh-Hant` | 2 |
| Korean | `ko` | 2 |
| Spanish | `es` | 2 |
| French | `fr` | 2 |
| German | `de` | 3 |
| Portuguese | `pt` | 3 |
| Arabic | `ar` | 3 |

### A.2 Localized Strings

```json
{
  "en": {
    "indicator_tooltip": "Source information provided",
    "l2_title": "Content Provenance",
    "l2_signer": "Signer",
    "l2_capture_time": "Capture Time",
    "l2_view_details": "View Details",
    "disclaimer_short": "This does not guarantee accuracy."
  },
  "ja": {
    "indicator_tooltip": "出所情報を提供している投稿です",
    "l2_title": "コンテンツ出自情報",
    "l2_signer": "署名者",
    "l2_capture_time": "撮影日時",
    "l2_view_details": "詳細を見る",
    "disclaimer_short": "正確性を保証するものではありません。"
  }
}
```

---

## Appendix B: Test Vectors

### B.1 Verification Timeout Test

```json
{
  "TestCase": "VerificationTimeout",
  "Input": {
    "MediaSize": "50MB",
    "ManifestPresent": true,
    "TimeoutSetting": "200ms"
  },
  "ExpectedBehavior": {
    "Result": "VERIFICATION_TIMEOUT",
    "Action": "SilentPassthrough",
    "UserNotification": "None",
    "ProcessedMedia": "Original unchanged"
  }
}
```

### B.2 No Manifest Test

```json
{
  "TestCase": "NoManifest",
  "Input": {
    "MediaType": "JPEG",
    "ManifestPresent": false
  },
  "ExpectedBehavior": {
    "Result": "PROVENANCE_UNAVAILABLE",
    "Action": "SilentPassthrough",
    "IndicatorApplied": false
  }
}
```

### B.3 Valid CPP Manifest Test

```json
{
  "TestCase": "ValidCPPManifest",
  "Input": {
    "MediaType": "JPEG",
    "ManifestType": "CPP",
    "ManifestVersion": "1.4",
    "SignatureValid": true
  },
  "ExpectedBehavior": {
    "Result": "PROVENANCE_AVAILABLE",
    "Action": "ApplyIndicator",
    "IndicatorTypes": ["VisualMark", "DynamicQR"]
  }
}
```

---

## Appendix C: Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-15 | Initial release |
| 1.1 | 2026-01-20 | TSA verification improvements |
| 1.2 | 2026-01-24 | AnchorDigest, MessageImprint verification |
| 1.3 | 2026-01-27 | Full Merkle tree specification |
| 1.4 | 2026-01-29 | Depth Analysis Extension, multi-platform support |
| 1.5 | 2026-01-30 | **Pre-Publish Verification Extension** |

---

## References

- RFC 2119 (Requirement Levels)
- RFC 3161 (Time-Stamp Protocol)
- RFC 5652 (CMS)
- RFC 6962 (Certificate Transparency - Merkle Trees)
- RFC 8785 (JSON Canonicalization Scheme)
- C2PA Specification v2.1
- C2PA UX Recommendations
- IETF SCITT Architecture (draft)
- Apple App Extension Programming Guide
- Android Intent and Intent Filters
- EU AI Act (Regulation 2024/1689)
- California AB 853 (AI Transparency Act)

---

**Copyright © 2026 VeritasChain Standards Organization. CC BY 4.0**
