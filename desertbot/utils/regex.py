try:
    import re2 as _re
except ImportError:
    import re as _re
    re = _re
else:
    import re as _std_re

    class RE2Wrapper:
        def __init__(self, re2_module, fallback_module):
            self._re2 = re2_module
            self._fallback = fallback_module

        def __getattr__(self, name):
            # Prefer re2, but fall back to stdlib re
            return getattr(self._re2, name, getattr(self._fallback, name))

    re = RE2Wrapper(_re, _std_re)

