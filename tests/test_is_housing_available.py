import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from checkUrl import is_housing_available


def test_is_housing_available_handles_empty_script():
    html = "<html><body><script type='application/json'></script></body></html>"
    assert is_housing_available(html, "http://example.com") is None
