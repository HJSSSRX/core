import pytest

from forhacker.security.sandbox import Sandbox


def test_sandbox_is_abc():
    with pytest.raises(TypeError):
        Sandbox()
