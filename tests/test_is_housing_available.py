import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from checkUrl import is_housing_available


def test_is_housing_available_handles_empty_script():
    html = "<html><body><script type='application/json'></script></body></html>"
    assert is_housing_available(html, "http://example.com") is None


def test_is_housing_available_detects_login_button():
    html = """
    <html>
        <body>
            <div class='fr-card__cta'>
                <button class='fr-btn'>Connectez-vous pour vérifier les disponibilités</button>
            </div>
        </body>
    </html>
    """
    assert is_housing_available(html, "http://example.com") is True


def test_is_housing_available_detects_missing_login_button_as_unavailable():
    html = """
    <html>
        <body>
            <div class='fr-card__cta'></div>
        </body>
    </html>
    """
    assert is_housing_available(html, "http://example.com") is False
