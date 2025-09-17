"""
Top-level package initializer for the backend source tree.

Having this file ensures Python treats the 'src' directory as a package,
which improves reliability of module imports such as 'src.api.main:app'
when running under different working directories or process managers.
"""
# PUBLIC_INTERFACE
def package_name() -> str:
    """Return the package name for diagnostics."""
    return "src"
