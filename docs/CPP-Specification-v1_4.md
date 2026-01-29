# Capture Provenance Profile (CPP) Specification

**Version:** 1.4  
**Status:** Released  
**Date:** 2026-01-29  
**Document ID:** VSO-CPP-SPEC-005  
**Maintainer:** VeritasChain Standards Organization (VSO)  
**License:** CC BY 4.0 International

---

## Abstract

The Capture Provenance Profile (CPP) is an open specification for cryptographically verifiable media capture provenance. Unlike edit-history approaches such as C2PA, CPP focuses on proving "this media was actually captured at this moment" with **deletion detection**, **external timestamping**, and **privacy-by-design** architecture.

CPP v1.4 adds the **Depth Analysis Extension** for screen detection and expands platform support to include **embedded systems**, **physical cameras**, **drones**, and **industrial imaging devices**.

---

## 1. Changes from v1.3

| Item | v1.3 | v1.4 | Rationale |
|------|------|------|-----------|
| **DepthAnalysis** | Not specified | OPTIONAL extension | Screen detection capability |
| **Platform scope** | Smartphone-focused | Cross-platform | Embedded/physical camera support |
| **DeviceInfo.DeviceClass** | Not specified | NEW field | Platform identification |
| **SensorType** | Not specified | 12 values defined | Platform-independent depth sensors |
| **CaptureDevice** | Not specified | NEW object | Physical camera metadata |

---

## 2. Platform Support

### 2.1 Supported Device Classes

CPP v1.4 is designed for implementation across diverse capture platforms:

| DeviceClass | Description | Examples |
|-------------|-------------|----------|
| `Smartphone` | Mobile phones with cameras | iPhone, Android phones |
| `Tablet` | Tablet devices | iPad, Android tablets |
| `DigitalCamera` | Dedicated digital cameras | DSLR, mirrorless, compact |
| `ActionCamera` | Rugged/action cameras | GoPro, DJI Action |
| `Drone` | Unmanned aerial vehicles | DJI Mavic, Autel |
| `Surveillance` | Fixed security cameras | IP cameras, CCTV |
| `BodyCamera` | Wearable body cameras | Axon, Motorola |
| `Dashcam` | Vehicle-mounted cameras | BlackVue, Garmin |
| `IndustrialCamera` | Machine vision/inspection | Basler, FLIR |
| `MedicalImaging` | Medical capture devices | Endoscopes, dermascopes |
| `Webcam` | Computer-attached cameras | Logitech, built-in |
| `Embedded` | Custom embedded systems | Raspberry Pi, Arduino |
| `Other` | Unclassified devices | Custom implementations |

### 2.2 DeviceInfo Extension

```json
{
  "DeviceInfo": {
    "Manufacturer": "Canon",
    "Model": "EOS R5",
    "DeviceClass": "DigitalCamera",
    "SerialNumber": "012345678901",
    "FirmwareVersion": "1.8.1",
    "CaptureDevice": {
      "SensorSize": "36x24mm",
      "SensorType": "CMOS",
      "LensInfo": "RF 24-70mm F2.8L",
      "FocalLength": 35,
      "Aperture": 2.8,
      "ISO": 400,
      "ShutterSpeed": "1/250"
    },
    "SecurityModule": {
      "Type": "TPM",
      "Version": "2.0",
      "Manufacturer": "Infineon"
    }
  }
}
```

### 2.3 CaptureDevice Object (OPTIONAL)

For physical cameras and professional imaging devices:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| SensorSize | string | NO | Physical sensor dimensions |
| SensorType | string | NO | CCD, CMOS, BSI-CMOS, etc. |
| LensInfo | string | NO | Lens model or description |
| FocalLength | float | NO | Focal length in mm |
| Aperture | float | NO | f-number |
| ISO | int | NO | ISO sensitivity |
| ShutterSpeed | string | NO | Exposure time |
| WhiteBalance | string | NO | White balance mode |
| ColorSpace | string | NO | sRGB, AdobeRGB, etc. |

### 2.4 SecurityModule Object (OPTIONAL)

For devices with hardware security:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Type | string | YES | TPM, SecureEnclave, HSM, TEE, SoftwareOnly |
| Version | string | NO | Module version |
| Manufacturer | string | NO | Security chip manufacturer |
| KeyAttestation | boolean | NO | Whether key attestation is supported |
| CertificateChain | array | NO | Certificate chain for key attestation |

---

## 3. Depth Analysis Extension (OPTIONAL)

### 3.1 Overview

The Depth Analysis Extension enables detection of whether the captured subject is a physical object or a digital screen (monitor, smartphone, tablet, etc.).

**Purpose:**
- Detect "screen capture" attacks where someone photographs a displayed image
- Provide evidence regarding the likelihood of screen vs. real-world subject
- Enhance verification in legal and forensic contexts

**Scope:**
- OPTIONAL extension (does not affect core CPP functionality)
- Applies to devices with depth sensors
- Results indicate likelihood, not definitive proof

### 3.2 SensorData.DepthAnalysis

```json
{
  "SensorData": {
    "GPS": { ... },
    "Accelerometer": [...],
    "Compass": 180.5,
    "DepthAnalysis": {
      "Available": true,
      "SensorType": "LiDAR",
      "FrameTimestamp": "2026-01-29T10:30:00.123Z",
      "Resolution": {
        "Width": 256,
        "Height": 192
      },
      "Statistics": {
        "MinDepth": 0.45,
        "MaxDepth": 3.82,
        "MeanDepth": 1.23,
        "StdDeviation": 0.87,
        "DepthRange": 3.37,
        "ValidPixelRatio": 0.92
      },
      "PlaneAnalysis": {
        "DominantPlaneRatio": 0.15,
        "DominantPlaneDistance": 1.05,
        "PlaneCount": 3,
        "LargestPlaneArea": 0.12
      },
      "ScreenDetection": {
        "IsLikelyScreen": false,
        "Confidence": 0.95,
        "Indicators": {
          "FlatnessScore": 0.12,
          "DepthUniformity": 0.08,
          "EdgeSharpness": 0.25,
          "ReflectivityAnomaly": false
        }
      },
      "AnalysisHash": "sha256:abc123..."
    }
  }
}
```

### 3.3 DepthAnalysis Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Available | boolean | YES | Whether depth analysis was performed |
| SensorType | string | YES | Sensor technology identifier |
| FrameTimestamp | ISO8601 | COND | Timestamp of depth frame (if Available=true) |
| Resolution | object | COND | Depth map resolution (if Available=true) |
| Statistics | object | COND | Statistical analysis (if Available=true) |
| PlaneAnalysis | object | COND | Plane detection results (if Available=true) |
| ScreenDetection | object | COND | Screen detection verdict (if Available=true) |
| AnalysisHash | string | COND | SHA-256 hash of depth data (if Available=true) |
| UnavailableReason | string | COND | Reason code (if Available=false) |

### 3.4 SensorType Values (Platform-Independent)

| Value | Category | Description |
|-------|----------|-------------|
| **Smartphone/Tablet** | | |
| `LiDAR` | Active | Light Detection and Ranging (iPhone Pro, iPad Pro) |
| `TrueDepth` | Active | Structured light (iOS Front camera, Face ID) |
| `ToF` | Active | Time-of-Flight sensor (Samsung, Huawei, Sony) |
| `StructuredLight` | Active | IR dot projector (Google Pixel 4) |
| `Stereo` | Passive | Dual camera depth estimation |
| **Physical Camera** | | |
| `DualPixelAF` | Passive | Dual-pixel autofocus depth (Canon, Sony DSLRs) |
| `PhaseDifferenceAF` | Passive | Phase-detection AF depth data |
| `ExternalLiDAR` | Active | External LiDAR module attached |
| `ExternalToF` | Active | External ToF sensor attached |
| **Industrial/Specialized** | | |
| `IndustrialLiDAR` | Active | Industrial-grade LiDAR (Velodyne, Ouster) |
| `IndustrialToF` | Active | Industrial ToF (Basler, IFM) |
| `StructuredLightScanner` | Active | 3D scanning systems |
| `Radar` | Active | Radar-based depth (automotive, drones) |
| `Ultrasonic` | Active | Ultrasonic distance sensors |
| `RGBD` | Active | RGB-D cameras (Intel RealSense, Kinect) |
| **Status** | | |
| `Unavailable` | N/A | No depth sensor available |
| `NotSupported` | N/A | Device has sensor but not supported |

### 3.5 UnavailableReason Codes

| Code | Description |
|------|-------------|
| `SENSOR_NOT_AVAILABLE` | Device has no depth sensor |
| `SENSOR_NOT_SUPPORTED` | Sensor exists but driver/support missing |
| `PRO_REQUIRED` | Feature requires premium subscription |
| `CAPTURE_FAILED` | Depth capture failed during operation |
| `PERMISSION_DENIED` | Sensor permission not granted |
| `HARDWARE_ERROR` | Sensor hardware malfunction |
| `CALIBRATION_REQUIRED` | Sensor requires calibration |
| `ENVIRONMENTAL` | Environmental conditions prevent capture |
| `DISABLED_BY_POLICY` | Disabled by device/enterprise policy |

### 3.6 Statistics Object

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| MinDepth | float | meters | Minimum valid depth value |
| MaxDepth | float | meters | Maximum valid depth value |
| MeanDepth | float | meters | Average depth |
| StdDeviation | float | meters | Standard deviation of depth |
| DepthRange | float | meters | MaxDepth - MinDepth |
| ValidPixelRatio | float | 0-1 | Ratio of valid depth pixels |

### 3.7 PlaneAnalysis Object

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| DominantPlaneRatio | float | 0-1 | Ratio of pixels on largest plane |
| DominantPlaneDistance | float | meters | Distance to dominant plane |
| PlaneCount | int | count | Number of detected planes |
| LargestPlaneArea | float | m² | Area of largest plane (OPTIONAL) |

### 3.8 ScreenDetection Object

| Field | Type | Description |
|-------|------|-------------|
| IsLikelyScreen | boolean | Final verdict (likelihood, not certainty) |
| Confidence | float | Confidence level (0-1) |
| Indicators | object | Individual detection indicators |

### 3.9 ScreenDetection.Indicators

| Field | Type | Threshold | Description |
|-------|------|-----------|-------------|
| FlatnessScore | float | >0.85 suggests screen | Surface flatness measure |
| DepthUniformity | float | >0.90 suggests screen | Depth value uniformity |
| EdgeSharpness | float | >0.80 suggests screen | Depth discontinuity sharpness |
| ReflectivityAnomaly | boolean | true suggests screen | Unusual reflectivity pattern |

---

## 4. Screen Detection Algorithm (INFORMATIVE)

### 4.1 Reference Implementation

```python
def is_likely_screen(analysis: DepthAnalysis) -> tuple[bool, float]:
    """
    Determine if subject is likely a digital screen.
    
    NOTE: This is a REFERENCE implementation. Implementations MAY use
    different algorithms as long as the output format conforms to spec.
    
    Returns:
        (is_likely_screen, confidence)
    """
    stats = analysis.statistics
    plane = analysis.plane_analysis
    
    # Criterion 1: Low depth variance (flat surface)
    flatness_score = 1.0 - min(stats.std_deviation / 0.5, 1.0)
    
    # Criterion 2: Dominant plane covers most of frame
    plane_dominance = plane.dominant_plane_ratio
    
    # Criterion 3: Narrow depth range
    depth_uniformity = 1.0 - min(stats.depth_range / 2.0, 1.0)
    
    # Criterion 4: Sharp rectangular edges
    edge_sharpness = detect_rectangular_edges(analysis)
    
    # Weighted score
    score = (
        flatness_score * 0.30 +
        plane_dominance * 0.25 +
        depth_uniformity * 0.25 +
        edge_sharpness * 0.20
    )
    
    is_screen = score > 0.70
    confidence = abs(score - 0.50) * 2
    
    return is_screen, confidence
```

### 4.2 Calibration Reference

| Scene Type | Typical StdDev | Typical PlaneRatio | Expected Verdict |
|------------|----------------|-------------------|------------------|
| Outdoor landscape | 5.0+ m | <0.20 | NOT screen |
| Indoor room | 1.0-3.0 m | 0.20-0.40 | NOT screen |
| Document on desk | 0.3-0.8 m | 0.30-0.50 | NOT screen |
| Person portrait | 0.5-1.5 m | 0.15-0.30 | NOT screen |
| Monitor display | <0.05 m | >0.85 | LIKELY screen |
| Smartphone screen | <0.02 m | >0.90 | LIKELY screen |
| Printed photo | 0.01-0.05 m | >0.80 | Possible false positive |

**Note:** Printed photos on flat surfaces may trigger false positives. The system reports confidence levels to allow human judgment.

---

## 5. Embedded Systems Implementation Guide

### 5.1 Minimum Requirements

For embedded implementations (physical cameras, IoT devices):

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | ARM Cortex-M4+ | ARM Cortex-A53+ |
| RAM | 256 KB | 1 MB+ |
| Flash/Storage | 512 KB | 4 MB+ |
| Crypto Acceleration | SHA-256 HW | SHA-256 + ECDSA HW |
| RTC | Battery-backed | GNSS-synced |
| Network | Optional | Ethernet/WiFi/LTE |

### 5.2 Key Storage Options

| Option | Security Level | Use Case |
|--------|----------------|----------|
| **TPM 2.0** | High | Industrial, surveillance |
| **Secure Element** | High | IoT, embedded |
| **ARM TrustZone** | Medium-High | Smartphones, tablets |
| **HSM (external)** | Very High | Enterprise, medical |
| **Software Keystore** | Medium | Development, testing |
| **ATECC608** | Medium-High | Low-power embedded |

### 5.3 Timestamping for Offline Devices

Devices without persistent network connectivity:

```
Option 1: Batch TSA Submission
  - Store events locally with device timestamp
  - Submit batch to TSA when connectivity available
  - TSA timestamp applies to batch hash

Option 2: GPS Time Source
  - Use GNSS receiver for accurate time
  - Record GNSS fix quality in metadata
  - Note: GPS time alone is not cryptographically verifiable

Option 3: Trusted Time Source
  - Synchronize with authenticated time server when online
  - Use secure RTC with tamper detection
  - Record last sync timestamp and drift estimate
```

### 5.4 Resource-Constrained Implementation

For devices with limited resources:

```c
// Minimal CPP Event (required fields only)
typedef struct {
    uint8_t  version;           // CPP version (0x14 for v1.4)
    uint8_t  event_type;        // 0x01=photo, 0x02=video_start, etc.
    uint32_t sequence_number;   // Sequential counter
    uint32_t timestamp;         // Unix timestamp (seconds)
    uint8_t  image_hash[32];    // SHA-256 of image
    uint8_t  device_key_id[8];  // Key identifier
    uint8_t  signature[64];     // ECDSA P-256 signature
} cpp_event_minimal_t;          // Total: 113 bytes

// Compact JSON alternative (~200 bytes)
{
  "v": "1.4",
  "t": "photo",
  "seq": 1234,
  "ts": 1738140000,
  "ih": "sha256:abc...",
  "sig": "..."
}
```

---

## 6. Physical Camera Integration

### 6.1 Digital Camera (DSLR/Mirrorless)

```json
{
  "CPPVersion": "1.4",
  "EventType": "PHOTO_CAPTURE",
  "DeviceInfo": {
    "Manufacturer": "Sony",
    "Model": "A7R V",
    "DeviceClass": "DigitalCamera",
    "SerialNumber": "1234567",
    "FirmwareVersion": "2.01",
    "CaptureDevice": {
      "SensorSize": "35.7x23.8mm",
      "SensorType": "BSI-CMOS",
      "LensInfo": "FE 24-70mm F2.8 GM II",
      "FocalLength": 50,
      "Aperture": 4.0,
      "ISO": 200,
      "ShutterSpeed": "1/500"
    },
    "SecurityModule": {
      "Type": "TPM",
      "Version": "2.0"
    }
  },
  "SensorData": {
    "GPS": {
      "Latitude": 35.6812,
      "Longitude": 139.7671,
      "Altitude": 40.0,
      "Accuracy": 3.0
    },
    "DepthAnalysis": {
      "Available": true,
      "SensorType": "DualPixelAF",
      "Statistics": {
        "MinDepth": 2.1,
        "MaxDepth": 15.3,
        "MeanDepth": 5.2,
        "StdDeviation": 3.1
      },
      "ScreenDetection": {
        "IsLikelyScreen": false,
        "Confidence": 0.94
      }
    }
  }
}
```

### 6.2 Drone Camera

```json
{
  "CPPVersion": "1.4",
  "EventType": "PHOTO_CAPTURE",
  "DeviceInfo": {
    "Manufacturer": "DJI",
    "Model": "Mavic 3 Pro",
    "DeviceClass": "Drone",
    "SerialNumber": "ABCD1234567890",
    "FirmwareVersion": "01.00.0500",
    "CaptureDevice": {
      "SensorSize": "17.3x13mm",
      "SensorType": "CMOS",
      "LensInfo": "Hasselblad 24mm F2.8",
      "FocalLength": 24,
      "Aperture": 2.8
    }
  },
  "SensorData": {
    "GPS": {
      "Latitude": 35.6812,
      "Longitude": 139.7671,
      "Altitude": 150.0,
      "Accuracy": 1.5
    },
    "FlightData": {
      "AltitudeAGL": 120.0,
      "Heading": 45.0,
      "Speed": 5.2,
      "GimbalPitch": -30.0,
      "GimbalRoll": 0.0,
      "GimbalYaw": 45.0
    },
    "Accelerometer": [0.02, 0.01, 9.81],
    "Gyroscope": [0.001, 0.002, -0.001]
  }
}
```

### 6.3 Surveillance Camera

```json
{
  "CPPVersion": "1.4",
  "EventType": "VIDEO_SEGMENT",
  "DeviceInfo": {
    "Manufacturer": "Axis",
    "Model": "P3255-LVE",
    "DeviceClass": "Surveillance",
    "SerialNumber": "ACCC8E123456",
    "FirmwareVersion": "11.8.64",
    "InstallationID": "SITE-A-CAM-03",
    "SecurityModule": {
      "Type": "TPM",
      "Version": "2.0",
      "Manufacturer": "Axis"
    }
  },
  "SensorData": {
    "GPS": {
      "Latitude": 35.6812,
      "Longitude": 139.7671,
      "FixedLocation": true
    },
    "DepthAnalysis": {
      "Available": false,
      "SensorType": "Unavailable",
      "UnavailableReason": "SENSOR_NOT_AVAILABLE"
    }
  },
  "VideoMetadata": {
    "Duration": 60.0,
    "FrameRate": 30,
    "Resolution": "3840x2160",
    "Codec": "H.265"
  }
}
```

### 6.4 Body Camera

```json
{
  "CPPVersion": "1.4",
  "EventType": "VIDEO_START",
  "DeviceInfo": {
    "Manufacturer": "Axon",
    "Model": "Body 4",
    "DeviceClass": "BodyCamera",
    "SerialNumber": "X12345678",
    "FirmwareVersion": "4.2.1",
    "AssignedTo": "OFFICER-ID-HASH",
    "SecurityModule": {
      "Type": "SecureElement",
      "KeyAttestation": true
    }
  },
  "AttestedCapture": {
    "Mode": "REQUIRED",
    "AttestationType": "PIN",
    "AttestationResult": "SUCCESS",
    "AttestationTimestamp": "2026-01-29T08:00:00.000Z"
  },
  "SensorData": {
    "GPS": {
      "Latitude": 35.6812,
      "Longitude": 139.7671,
      "Accuracy": 5.0
    },
    "Accelerometer": [0.1, 0.2, 9.78]
  }
}
```

---

## 7. Privacy Considerations

### 7.1 Depth Analysis Data Minimization

- Raw depth map is NOT stored in CPP events
- Only statistical summaries are recorded
- AnalysisHash proves computation without storing data
- No 3D reconstruction or facial geometry extracted

### 7.2 Location Data Defaults

| DeviceClass | GPS Default | Rationale |
|-------------|-------------|-----------|
| Smartphone | OFF | User privacy |
| Tablet | OFF | User privacy |
| DigitalCamera | OFF | User privacy |
| Drone | ON | Regulatory requirement |
| Surveillance | ON | Fixed location context |
| BodyCamera | ON | Accountability |
| Dashcam | ON | Incident documentation |

### 7.3 Serial Number Handling

Implementations SHOULD:
- Hash serial numbers before sharing
- Provide option to omit serial numbers
- Never expose serial numbers in public proofs

---

## 8. Conformance Levels

### 8.1 Level Definitions

| Level | Core | TSA | Merkle | Depth | Attestation |
|-------|------|-----|--------|-------|-------------|
| CPP-BASIC | ✓ | - | - | - | - |
| CPP-TIMESTAMPED | ✓ | ✓ | - | - | - |
| CPP-STANDARD | ✓ | ✓ | ✓ | - | - |
| CPP-ENHANCED | ✓ | ✓ | ✓ | ✓ | - |
| CPP-FULL | ✓ | ✓ | ✓ | ✓ | ✓ |

### 8.2 Embedded Conformance

For resource-constrained devices:

| Level | Minimum Resources | Offline Capable |
|-------|-------------------|-----------------|
| CPP-BASIC | 64KB RAM | Yes |
| CPP-TIMESTAMPED | 128KB RAM | No (requires TSA) |
| CPP-STANDARD | 256KB RAM | Partial (batch TSA) |
| CPP-ENHANCED | 1MB RAM + Depth | Partial |
| CPP-FULL | 1MB RAM + Biometric | No |

---

## 9. Security Considerations

### 9.1 Depth Analysis Limitations

Depth analysis provides ADDITIONAL evidence, not definitive proof:

- **False positives possible:** Printed photos, flat artwork, whiteboards
- **False negatives possible:** Curved monitors, reflective screens
- **Environmental factors:** Lighting, distance, angle affect accuracy
- **Human review recommended:** For high-stakes verification

### 9.2 Physical Camera Security

| Threat | Mitigation |
|--------|------------|
| Key extraction | Use TPM/HSM, disable JTAG |
| Firmware tampering | Secure boot, signed updates |
| Clock manipulation | Battery-backed RTC, GNSS sync |
| Replay attacks | Sequence numbers, event chaining |
| Physical tampering | Tamper-evident seals, sensors |

### 9.3 Embedded Device Considerations

- Assume physical access is possible
- Use hardware security modules where available
- Implement tamper detection where possible
- Document security boundaries in deployment guide

---

## 10. Verification

### 10.1 Depth Analysis Display

Verifiers SHOULD display:
- Screen detection verdict with confidence level
- Key indicators (flatness, uniformity, edge sharpness)
- Warning if confidence < 0.80
- Clear indication that result is "likelihood" not "certainty"

### 10.2 Platform-Specific Notes

Verifiers SHOULD note:
- Device class and manufacturer
- Security module type and attestation status
- Location data source and accuracy
- Any fields marked as unavailable

---

## 11. Examples

### 11.1 Smartphone (Real-World Scene)

```json
{
  "CPPVersion": "1.4",
  "EventType": "PHOTO_CAPTURE",
  "DeviceInfo": {
    "Manufacturer": "Apple",
    "Model": "iPhone 15 Pro",
    "DeviceClass": "Smartphone",
    "OSVersion": "iOS 18.2"
  },
  "SensorData": {
    "DepthAnalysis": {
      "Available": true,
      "SensorType": "LiDAR",
      "Statistics": {
        "MinDepth": 0.8,
        "MaxDepth": 5.2,
        "MeanDepth": 2.1,
        "StdDeviation": 1.4,
        "DepthRange": 4.4,
        "ValidPixelRatio": 0.95
      },
      "ScreenDetection": {
        "IsLikelyScreen": false,
        "Confidence": 0.92,
        "Indicators": {
          "FlatnessScore": 0.15,
          "DepthUniformity": 0.08,
          "EdgeSharpness": 0.12,
          "ReflectivityAnomaly": false
        }
      },
      "AnalysisHash": "sha256:a1b2c3..."
    }
  }
}
```

### 11.2 Smartphone (Screen Detected)

```json
{
  "SensorData": {
    "DepthAnalysis": {
      "Available": true,
      "SensorType": "LiDAR",
      "Statistics": {
        "MinDepth": 0.52,
        "MaxDepth": 0.58,
        "MeanDepth": 0.55,
        "StdDeviation": 0.02,
        "DepthRange": 0.06,
        "ValidPixelRatio": 0.98
      },
      "ScreenDetection": {
        "IsLikelyScreen": true,
        "Confidence": 0.96,
        "Indicators": {
          "FlatnessScore": 0.96,
          "DepthUniformity": 0.97,
          "EdgeSharpness": 0.88,
          "ReflectivityAnomaly": false
        }
      }
    }
  }
}
```

### 11.3 Depth Unavailable (Non-Pro Device)

```json
{
  "SensorData": {
    "DepthAnalysis": {
      "Available": false,
      "SensorType": "Unavailable",
      "UnavailableReason": "SENSOR_NOT_AVAILABLE"
    }
  }
}
```

### 11.4 Industrial Camera

```json
{
  "CPPVersion": "1.4",
  "EventType": "PHOTO_CAPTURE",
  "DeviceInfo": {
    "Manufacturer": "Basler",
    "Model": "acA4112-30uc",
    "DeviceClass": "IndustrialCamera",
    "SerialNumber": "40012345",
    "FirmwareVersion": "3.2.0",
    "SecurityModule": {
      "Type": "HSM",
      "Manufacturer": "Thales"
    }
  },
  "SensorData": {
    "DepthAnalysis": {
      "Available": true,
      "SensorType": "IndustrialToF",
      "Statistics": {
        "MinDepth": 0.3,
        "MaxDepth": 0.5,
        "MeanDepth": 0.4,
        "StdDeviation": 0.02
      },
      "ScreenDetection": {
        "IsLikelyScreen": false,
        "Confidence": 0.89
      }
    }
  }
}
```

---

## Appendix A: Device Compatibility Matrix

### A.1 Smartphone/Tablet

| Device | DepthSensor | SensorType | Notes |
|--------|-------------|------------|-------|
| iPhone 12 Pro+ | LiDAR | `LiDAR` | Back camera |
| iPhone X+ | TrueDepth | `TrueDepth` | Front camera only |
| iPhone (non-Pro) | None | `Unavailable` | |
| iPad Pro (2020+) | LiDAR | `LiDAR` | |
| Samsung Galaxy S20+ Ultra | ToF | `ToF` | |
| Samsung Galaxy S21-S24 Ultra | Laser AF | `ToF` | |
| Google Pixel 4/4 XL | IR Projector | `StructuredLight` | |
| Huawei P30/Mate 30 Pro | ToF | `ToF` | |
| Devices with dual cameras | Stereo | `Stereo` | Software depth |

### A.2 Digital Cameras

| Device | DepthSensor | SensorType | Notes |
|--------|-------------|------------|-------|
| Canon EOS R5/R6 | Dual Pixel CMOS AF | `DualPixelAF` | Limited depth info |
| Sony A7R V | Phase Detection AF | `PhaseDifferenceAF` | AF point depth |
| Nikon Z8/Z9 | Phase Detection AF | `PhaseDifferenceAF` | |
| Most DSLRs | None | `Unavailable` | Contrast AF only |

### A.3 Action/Drone Cameras

| Device | DepthSensor | SensorType | Notes |
|--------|-------------|------------|-------|
| GoPro Hero 12 | None | `Unavailable` | |
| DJI Mavic 3 | Vision sensors | `Stereo` | Obstacle avoidance |
| DJI Mini 4 | None | `Unavailable` | |
| Insta360 X4 | None | `Unavailable` | |

### A.4 Specialized Cameras

| Device | DepthSensor | SensorType | Notes |
|--------|-------------|------------|-------|
| Intel RealSense D455 | Stereo IR | `RGBD` | |
| Microsoft Azure Kinect | ToF | `RGBD` | |
| Velodyne Puck | LiDAR | `IndustrialLiDAR` | |
| IFM O3D | ToF | `IndustrialToF` | |

---

## Appendix B: Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-15 | Initial release |
| 1.1 | 2026-01-20 | TSA verification improvements |
| 1.2 | 2026-01-24 | AnchorDigest, MessageImprint verification |
| 1.3 | 2026-01-27 | Full Merkle tree specification |
| 1.4 | 2026-01-29 | Depth Analysis Extension, multi-platform support |

---

## Appendix C: Merkle Tree Construction (From v1.3)

CPP v1.4 inherits all Merkle tree construction rules from v1.3:

- LeafHash = SHA256(EventHash_bytes)
- LeafHashMethod = "SHA256(EventHash)"
- Pairing rule: SHA256(Left || Right)
- Index interpretation: Even=Left, Odd=Right
- Padding rule: Duplicate last leaf
- Proof direction: Bottom to Top

See CPP v1.3 Specification for complete Merkle tree details.

---

## References

- RFC 2119 (Requirement Levels)
- RFC 3161 (Time-Stamp Protocol)
- RFC 5652 (CMS)
- RFC 6962 (Certificate Transparency - Merkle Trees)
- RFC 8785 (JSON Canonicalization Scheme)
- FIPS 186-5 (ECDSA)
- ISO/IEC 11889 (TPM 2.0)
- GlobalPlatform TEE Specification

---

**Copyright © 2026 VeritasChain Standards Organization. CC BY 4.0**
