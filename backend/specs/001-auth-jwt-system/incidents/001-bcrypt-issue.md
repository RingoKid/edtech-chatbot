# bcrypt Version Compatibility Issue - Resolution

**Date:** 2025-11-10
**Issue:** Unit tests failing with `ValueError: password cannot be longer than 72 bytes`
**Root Cause:** Incompatibility between passlib 1.7.4 and bcrypt 5.0.0

---

## What is bcrypt?

**bcrypt** is a cryptographic password hashing algorithm specifically designed for securely storing passwords.

### Key Characteristics:

1. **Adaptive Hashing (Slow by Design)**
   - Intentionally computationally expensive
   - Takes ~100-300ms to hash a single password
   - Makes brute-force attacks impractical
   - Cost factor can be adjusted as computers get faster

2. **Automatic Salt Generation**
   - Creates a unique random salt for each password
   - Salt is embedded in the hash output
   - Prevents rainbow table attacks
   - No need to store salt separately

3. **One-Way Function**
   - Cannot be reversed to get original password
   - Can only verify by hashing the input and comparing

4. **Built-in Work Factor**
   - Default is 12 rounds (2^12 = 4,096 iterations)
   - Each round doubles the computation time
   - Can be increased as hardware improves

5. **72-Byte Password Limit**
   - bcrypt can only hash the first 72 bytes of a password
   - Anything beyond 72 bytes is ignored
   - This is a fundamental limitation of the Blowfish algorithm

### How bcrypt Works in Our Code:

```python
from passlib.context import CryptContext

# Initialize password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashing a password
hashed = pwd_context.hash("mypassword")
# Output: $2b$12$KIXl234...
#         ^   ^   ^
#         |   |   |_ Random salt + hash
#         |   |_____ Work factor (12 = 2^12 iterations)
#         |_________ Algorithm version ($2b = bcrypt)

# Verifying a password
is_valid = pwd_context.verify("mypassword", hashed)  # Returns True
is_valid = pwd_context.verify("wrongpass", hashed)   # Returns False
```

### Hash Format Breakdown:

```
$2b$12$N9qo8uLOickgx2ZMRZoMye.IjSLGPXzBNnK8jLNfg/1XqYxJ.kQGq
│  │  │                                               │
│  │  └─ Salt (22 chars)                             └─ Hash (31 chars)
│  └──── Work factor (cost)
└─────── Algorithm identifier ($2b = bcrypt)
```

---

## The Problem We Encountered

### Error Message:
```
ValueError: password cannot be longer than 72 bytes,
truncate manually if necessary (e.g. my_password[:72])
```

### Root Cause:

**Version Incompatibility:**
- **passlib 1.7.4** (released 2020, last update 4+ years ago)
- **bcrypt 5.0.0** (latest version, released 2024)

### What Happened:

1. **requirements.txt specified:**
   ```txt
   passlib[bcrypt]>=1.7.4
   ```

2. **pip installed:**
   - passlib 1.7.4 ✅
   - bcrypt 5.0.0 ✅ (latest version, but incompatible!)

3. **During passlib initialization:**
   - passlib runs an internal test to detect bcrypt "wrap-around bug"
   - This test uses a 256-byte password
   - bcrypt 5.0.0 now strictly enforces 72-byte limit
   - Test fails with ValueError

### Changes in bcrypt 5.0.0:

1. **Removed `__about__` module**
   - passlib expects this module to check bcrypt version
   - Causes warning: `AttributeError: module 'bcrypt' has no attribute '__about__'`

2. **Strict 72-byte password limit**
   - Previous versions silently truncated passwords > 72 bytes
   - Version 5.0.0 raises ValueError instead
   - More secure (prevents silent truncation) but breaks passlib

### Why passlib Uses Long Test Passwords:

bcrypt had a historical bug where extremely long passwords (>255 bytes) would "wrap around" and produce weak hashes. passlib tests for this bug during initialization, but the test itself now fails with bcrypt 5.0.0.

---

## The Solution

### Fix Applied:

**Pin bcrypt to version 4.x** which is compatible with passlib 1.7.4:

```txt
# requirements.txt
passlib[bcrypt]>=1.7.4
bcrypt>=4.0.0,<5.0.0  # Pin to 4.x for passlib compatibility
email-validator>=2.0.0  # Also added - required for pydantic EmailStr
```

### Installation:

```bash
pip install "bcrypt>=4.0.0,<5.0.0" --force-reinstall
```

### Verification:

```bash
$ pip show bcrypt | grep Version
Version: 4.3.0  ✅

$ pytest tests/unit/test_security.py -v
tests/unit/test_security.py::test_password_hashing PASSED
tests/unit/test_security.py::test_create_access_token PASSED
tests/unit/test_security.py::test_create_refresh_token PASSED
tests/unit/test_security.py::test_decode_invalid_token PASSED
tests/unit/test_security.py::test_decode_expired_token PASSED

5 passed ✅
```

---

## Additional Missing Dependency

### email-validator

**Error:**
```
ImportError: email-validator is not installed,
run `pip install 'pydantic[email]'`
```

**Cause:**
- `app/schemas/auth.py` uses `EmailStr` type from pydantic
- `EmailStr` requires `email-validator` package
- Not included in original requirements.txt

**Fix:**
```txt
# requirements.txt
email-validator>=2.0.0  # Required for pydantic EmailStr
```

**Installation:**
```bash
pip install 'pydantic[email]'
# This installs email-validator and dnspython
```

---

## Warnings (Non-Critical)

### Deprecation Warning:

```
DeprecationWarning: 'crypt' is deprecated and slated for removal in Python 3.13
```

**Impact:** Low - This is a passlib warning, not an error
**Cause:** passlib uses the `crypt` module as a fallback
**Action:** None needed for now. passlib may need updating when Python 3.13 is released.

---

## Why This Matters for Security

### bcrypt's 72-byte limit is NOT a weakness:

1. **72 bytes = 72 characters** (for ASCII passwords)
2. **Entropy calculation:**
   - Strong password: 12-16 characters
   - 72-character password has astronomical entropy
   - No human remembers 72-character passwords anyway

3. **Best practices:**
   - Use passwords 12-20 characters
   - Mix uppercase, lowercase, numbers, symbols
   - All fall well under 72-byte limit

### What if users enter >72 byte passwords?

**Option 1: Pre-hash before bcrypt (Not done in our implementation)**
```python
import hashlib
# Hash long passwords before bcrypt
prehashed = hashlib.sha256(long_password.encode()).hexdigest()
bcrypt_hash = pwd_context.hash(prehashed)
```

**Option 2: Reject long passwords (Simpler, recommended)**
```python
# In UserCreate schema
password: str = Field(..., min_length=8, max_length=72)
```

**Current implementation:** Relies on bcrypt 4.x silently truncating (acceptable for most use cases)

---

## Test Results

### Before Fix:
```
tests/unit/test_security.py::test_password_hashing FAILED
ValueError: password cannot be longer than 72 bytes
```

### After Fix:
```
tests/unit/test_security.py::test_password_hashing PASSED ✅
tests/unit/test_security.py::test_create_access_token PASSED ✅
tests/unit/test_security.py::test_create_refresh_token PASSED ✅
tests/unit/test_security.py::test_decode_invalid_token PASSED ✅
tests/unit/test_security.py::test_decode_expired_token PASSED ✅

5 passed, 1 warning in 1.37s
```

---

## Long-Term Considerations

### passlib is Semi-Abandoned:

- Last release: 2020
- No active development
- Python 3.13 compatibility uncertain

### Future Migration Options:

1. **Use bcrypt directly** (when ready to migrate):
   ```python
   import bcrypt

   # Hash password
   hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

   # Verify password
   is_valid = bcrypt.checkpw(password.encode(), hashed)
   ```

2. **Use argon2** (modern alternative):
   - Winner of Password Hashing Competition 2015
   - Better against GPU/ASIC attacks
   - More configurable than bcrypt
   - `passlib` also supports it

3. **Stay on passlib + bcrypt 4.x** (current choice):
   - Works well for now
   - Widely used and battle-tested
   - Migration can wait

---

## Summary

### What We Fixed:
1. ✅ Pinned bcrypt to 4.x for compatibility
2. ✅ Added email-validator dependency
3. ✅ All security tests passing

### What We Learned:
1. bcrypt is a strong, slow, password hashing algorithm
2. passlib is a wrapper that's not actively maintained
3. Version pinning is critical for cryptographic dependencies
4. bcrypt has a 72-byte limit (not a problem in practice)

### Next Steps:
1. Monitor passlib for Python 3.13 compatibility
2. Consider migrating to bcrypt directly in future
3. Document password requirements (if adding max length)

---

## References

- **bcrypt Algorithm:** https://en.wikipedia.org/wiki/Bcrypt
- **passlib Documentation:** https://passlib.readthedocs.io/
- **bcrypt Python Library:** https://github.com/pyca/bcrypt/
- **Password Hashing Competition:** https://www.password-hashing.net/
