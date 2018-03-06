import hulk
from hulk import Client


def test_url():
    base_url = "127.0.0.1:6000"
    path_a = "/languages"
    path_b = "languages"
    client = Client(base_url)

    url_a = client._url(path_a)
    url_b = client._url(path_b)
    expected_url = "{}/languages".format(base_url)

    assert url_a == expected_url
    assert url_b == expected_url
