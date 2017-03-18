# yakc

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/609f8fbe1f6944c097f9fbb9eec852ac)](https://www.codacy.com/app/douglas/yakc?utm_source=github.com&utm_medium=referral&utm_content=zuzak/yakc&utm_campaign=badger)

Displays a random webm from a large collection, and prompts users to moderate
them as good or bad, for future use.

One can vist `/` for a random unmoderated webm, or `/good` and `/bad` to
view moderated ones. Quorum is one; this may change at a later date.

Users can also report particularly bad webms, which will immediately
remove them from rotation and prevent them from being served.

For MD5 lookup to work, you need to precompute the hashes.
To do so, run `md5sum all/*.webm | tee md5.txt`.

# Settings
Run as *e.g.* `WEBM_CONFIG=settings.cfg python3 app.py`.

Example settings file:
```python
SERVER_NAME="webm.website"
DEBUG=False
```
