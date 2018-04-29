import pytest
import boggart
from boggart import Client


@pytest.mark.skip(reason="attempts to connect to server")
def test_constructor():
    # attempt to pass a URL without a scheme to the Client constructor
    bad_url = "127.0.0.1:6000"
    with pytest.raises(ValueError, message="expecting ValueError"):
        Client(bad_url)


@pytest.mark.skip(reason="attempts to connect to server")
def test_url():
    base_url = "https://127.0.0.1:6000"
    client = Client(base_url)
    actual_url = client._url("/languages")
    expected_url = "{}/languages".format(base_url)
    assert actual_url == expected_url
