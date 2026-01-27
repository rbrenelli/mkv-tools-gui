## 2026-01-27 - Supply Chain Security: Dependency Verification
**Vulnerability:** External binaries (FFmpeg, MKVToolNix) were downloaded from remote URLs without checksum verification.
**Learning:** Reliance on external URLs (even HTTPS) exposes the application to supply chain attacks if the upstream server is compromised or DNS is spoofed. "Latest" version links are particularly dangerous as they change content without URL changes, making verification impossible and builds non-reproducible.
**Prevention:**
1.  **Pin Versions:** Always link to specific, immutable version artifacts, not "latest".
2.  **Verify Checksums:** Calculate SHA256 hashes of known good binaries and enforce them in the code.
3.  **Fail Closed:** If a hash mismatch occurs, abort the process and delete the file immediately.
