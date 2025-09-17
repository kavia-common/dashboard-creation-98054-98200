"""API package initialization for BackendAPIService.

This module marks the directory as a Python package and can be used
for package-level exports if needed in the future.
"""
# PUBLIC_INTERFACE
def package_info():
    """Return brief info about the API package."""
    return {"name": "BackendAPIService API", "version_hint": "see settings.APP_VERSION"}
