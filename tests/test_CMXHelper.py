import pytest
import cmx
import ipaddress

@pytest.fixture
def client():
    cmx.app.config['TESTING'] = True
    client = cmx.app.test_client()

    yield client


def test_get_mac(client):
    """Test CMX mac to ip function Guest 10.21.0.0/16 Noc 10.16.0.0/22"""

    find_mac = False
    for i in range(2):
        mac = cmx.CMX.get_mac('10.21.0.{}'.format(i))
        print(i, mac)
        if mac != '00:00:00:00:00:00':
            find_mac = True

    assert find_mac