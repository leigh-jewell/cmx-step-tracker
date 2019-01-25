MOCK_USERS = [{"email": "test@example.com", "salt": "8Fb23mMNHD5Zb8pr2qWA3PE9bH0=", "hashed":
               "1736f83698df3f8153c1fbd6ce2840f8aace4f200771a46672635374073cc876cf0aa6a31f780e576578f791b5555b50df46303f0c3a7f2d21f91aa1429ac22e"},
              {"email": "test1@example.com", "salt": "8Fb23mMNHD5Zb8pr2qWA3PE9bH0=", "hashed":
                  "1736f83698df3f8153c1fbd6ce2840f8aace4f200771a46672635374073cc876cf0aa6a31f780e576578f791b5555b50df46303f0c3a7f2d21f91aa1429ac22e"},
              {"email": "test2@example.com", "salt": "8Fb23mMNHD5Zb8pr2qWA3PE9bH0=", "hashed":
                  "1736f83698df3f8153c1fbd6ce2840f8aace4f200771a46672635374073cc876cf0aa6a31f780e576578f791b5555b50df46303f0c3a7f2d21f91aa1429ac22e"}]


MOCK_DEVICE = [{"mac": "00:01:2a:01:00:1e", "owner":"test@example.com"},
                 {"mac": "00:01:2a:01:00:2f", "owner":"test1@example.com"},
                 {"mac": "00:01:2a:01:00:10", "owner":"test2@example.com"}]


MOCK_DISTANCE = [{"mac": "00:01:2a:01:00:1e", "mtrs":4075.95},
                 {"mac": "00:01:2a:01:00:2f", "mtrs": 1532.18},
                 {"mac": "00:01:2a:01:00:10", "mtrs": 1893.01}]


class MockDBHelper:

    def get_user(self, email):
        user = [x for x in MOCK_USERS if x.get("email") == email]
        if user:
            return user[0]
        return None

    def add_user(self, email, salt, hashed):
        MOCK_USERS.append({"email": email, "salt": salt, "hashed": hashed})

    def get_devices(self, email):
        result = []
        if len(MOCK_DEVICE) > 0:
            for row in (item for item in MOCK_DEVICE if email in item['owner']):
                for mac in (item for item in MOCK_DISTANCE if item['mac'] in row['mac']):
                    result.append(mac)
                    print(mac)
        return result

    def get_num_devices(self, number):
        results = []
        for devices in MOCK_DEVICE[1:number+1]:
            for distance in MOCK_DISTANCE:
                if devices['mac'] == distance['mac']:
                    results.append({"mac":devices['mac'], "owner":devices['owner'], "mtrs":distance['mtrs']})
        print(results)

        return results

    def add_device(self, mac, email):
        if not {"mac": mac, "owner": email} in MOCK_DEVICE:
            MOCK_DEVICE.append(
                {"mac": mac, "owner": email})
        return mac

    def delete_device(self, mac):
        for i, table in enumerate(MOCK_DEVICE):
            if table.get("mac") == mac:
                del MOCK_DEVICE[i]
                break
