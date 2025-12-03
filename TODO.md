# Fix Embedding DNS Error

## Issue
- DNS resolution failure for AIPIPE_BASE_URL (https://aipipe.org/)
- Error: [Errno 11001] getaddrinfo failed

## Solution
- Switch to local embeddings using sentence-transformers
- Added sentence-transformers to requirements.txt
- Installed sentence-transformers package

## Completed Steps
- [x] Added sentence-transformers to requirements.txt
- [x] Installed sentence-transformers package

## Completed Steps
- [x] Added sentence-transformers to requirements.txt
- [x] Installed sentence-transformers package
- [x] Set USE_REMOTE_EMBEDDING=False in .env file to force local embeddings
- [x] Verified embeddings work with local model (component tests pass)

## Remaining Issue
- LLM generation still failing with DNS error for AIPIPE_BASE_URL
- Need to fix AIPIPE_BASE_URL or use alternative LLM service

## Completed Steps
- [x] Created comprehensive .gitignore file for Python Django project
- [x] Included patterns for Python, Django, vector stores, embeddings cache, environments, IDEs, OS files
- [x] Added patterns to ignore documentation files (*.md, *.pdf) except essential ones (README.md, requirements.txt)
- [x] Ensured test_full_application.py is not ignored (as it's a Python file, not documentation)
- [x] Created comprehensive README.md with project overview, setup instructions, API documentation, and usage examples

## Next Steps
- [ ] Update AIPIPE_BASE_URL to https://aipipe.org/openrouter/v1 in .env file
- [ ] Test full pipeline with corrected AIPIPE configuration
- [ ] Verify LLM generation works with proper AIPIPE setup
