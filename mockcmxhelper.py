MOCK_MAC = [{"ip":"127.0.0.1", "mac":"00:01:2a:01:00:1e"}]

class MockCMXHelper:

    def get_mac(self, ip):
        mac = [x for x in MOCK_MAC if x.get("ip") == ip]
        if mac:
            return mac[0]['mac']
        return None
