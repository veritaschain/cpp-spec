#!/usr/bin/env python3
"""
CPP Completeness Invariant Reference Implementation

This is a reference implementation for educational purposes.
For production use, see the official SDKs.

Copyright (c) 2026 VeritasChain Standards Organization
Licensed under Apache 2.0
"""

import hashlib
import json
from typing import List, Dict, Tuple

def sha256_hex(data: bytes) -> str:
    """Compute SHA-256 hash and return as hex string."""
    return hashlib.sha256(data).hexdigest()

def canonicalize(obj: dict) -> bytes:
    """
    RFC 8785 JSON Canonicalization Scheme (simplified).
    
    For production, use a proper JCS library.
    """
    def sort_dict(d):
        if isinstance(d, dict):
            return {k: sort_dict(v) for k, v in sorted(d.items())}
        elif isinstance(d, list):
            return [sort_dict(x) for x in d]
        return d
    
    sorted_obj = sort_dict(obj)
    return json.dumps(sorted_obj, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def compute_event_hash(event: dict) -> bytes:
    """Compute hash of a CPP event (excluding signature)."""
    event_copy = {k: v for k, v in event.items() if k != 'signature'}
    canonical = canonicalize(event_copy)
    return hashlib.sha256(canonical).digest()

def xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR two byte arrays of equal length."""
    return bytes(x ^ y for x, y in zip(a, b))

def compute_completeness_invariant(events: List[dict]) -> dict:
    """
    Compute Completeness Invariant for a list of events.
    
    Returns:
        dict with expected_count and hash_sum
    """
    if not events:
        raise ValueError("Events list cannot be empty")
    
    hash_sum = bytes(32)  # Start with all zeros
    
    for event in events:
        event_hash = compute_event_hash(event)
        hash_sum = xor_bytes(hash_sum, event_hash)
    
    timestamps = [e['timestamp'] for e in events]
    
    return {
        'expected_count': len(events),
        'hash_sum': f"sha256:{hash_sum.hex()}",
        'first_timestamp': min(timestamps),
        'last_timestamp': max(timestamps),
        'first_event_id': events[0]['event_id'],
        'last_event_id': events[-1]['event_id']
    }

def verify_completeness_invariant(
    events: List[dict], 
    stored_ci: dict
) -> Tuple[bool, str]:
    """
    Verify Completeness Invariant against stored values.
    
    Returns:
        Tuple of (is_valid, message)
    """
    # Check 1: Event count
    if len(events) != stored_ci['expected_count']:
        return False, f"Count mismatch: expected {stored_ci['expected_count']}, got {len(events)}"
    
    # Check 2: Compute hash sum
    hash_sum = bytes(32)
    for event in events:
        event_hash = compute_event_hash(event)
        hash_sum = xor_bytes(hash_sum, event_hash)
    
    computed_hash_sum = f"sha256:{hash_sum.hex()}"
    if computed_hash_sum != stored_ci['hash_sum']:
        return False, f"Hash sum mismatch: computed {computed_hash_sum}"
    
    # Check 3: Timestamps
    timestamps = [e['timestamp'] for e in events]
    if min(timestamps) != stored_ci['first_timestamp']:
        return False, "First timestamp mismatch"
    if max(timestamps) != stored_ci['last_timestamp']:
        return False, "Last timestamp mismatch"
    
    # Check 4: Event IDs
    if events[0]['event_id'] != stored_ci['first_event_id']:
        return False, "First event ID mismatch"
    if events[-1]['event_id'] != stored_ci['last_event_id']:
        return False, "Last event ID mismatch"
    
    return True, "Completeness Invariant valid"


# Example usage
if __name__ == "__main__":
    # Create sample events
    events = [
        {
            "cpp_version": "1.0",
            "event_id": "event-001",
            "event_type": "CPP_CAPTURE",
            "timestamp": "2026-01-18T10:00:00.000Z",
            "payload": {"media_hash": "sha256:abc"}
        },
        {
            "cpp_version": "1.0",
            "event_id": "event-002",
            "event_type": "CPP_CAPTURE",
            "timestamp": "2026-01-18T11:00:00.000Z",
            "payload": {"media_hash": "sha256:def"}
        },
        {
            "cpp_version": "1.0",
            "event_id": "event-003",
            "event_type": "CPP_CAPTURE",
            "timestamp": "2026-01-18T12:00:00.000Z",
            "payload": {"media_hash": "sha256:ghi"}
        }
    ]
    
    # Compute CI
    ci = compute_completeness_invariant(events)
    print("Computed Completeness Invariant:")
    print(json.dumps(ci, indent=2))
    
    # Verify (should pass)
    is_valid, msg = verify_completeness_invariant(events, ci)
    print(f"\nVerification with all events: {is_valid} - {msg}")
    
    # Simulate deletion attack
    tampered_events = [events[0], events[2]]  # Missing event-002
    is_valid, msg = verify_completeness_invariant(tampered_events, ci)
    print(f"Verification with deleted event: {is_valid} - {msg}")
