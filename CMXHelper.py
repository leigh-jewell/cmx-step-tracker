import requests
requests.packages.urllib3.disable_warnings()
from requests.auth import HTTPBasicAuth
import json
import hashlib
import ipaddress


class CMXHelper:

    def __init__(self, app):
        self.app = app
        try:
            self.url = app.config['CMX_IP2MAC_URL']
        except:
            self.url = 'http://{}/api/location/v2/clients?ipAddress='
        try:
            cmx_list_str = app.config['CMX_HOST']
            self.app.logger.debug("CMX Helper init: got string {}".format(cmx_list_str))
            self.cmx_list = [v.strip() for v in cmx_list_str.split(',')]
            self.app.logger.debug("CMX Helper init: got list of cmx".format(self.cmx_list))
        except Exception as e:
            self.app.logger.error("CMX Helper init: no cmx list or not JSON: %s", e)
            self.cmx_list = []
        try:
            self.username = app.config['CMX_USERNAME']
        except:
            self.app.logger.error("CMX Helper init: config missing CMX_USERNAME: %s", e)
            self.username = ""
        try:
            self.password = app.config['CMX_PASSWORD']
        except:
            self.app.logger.error("CMX Helper init: config missing CMX_PASSWORD: %s", e)
            self.password = ""
        try:
            self.hash = app.config['CMX_MAC_HASH']
        except:
            self.app.logger.info("CMX Helper init: config missing CMX_HASH, assuming hash not used: %s", e)
            self.hash = ""
        try:
            self.timeout = app.config['CMX_TIMEOUT']
        except:
            self.timeout = 5

    def ip_to_mac(self, ip):
        ip_to_list = [int(i) for i in str(int(ip))]
        ip_to_list = [0] * (10 - len(ip_to_list)) + ip_to_list
        octets = [ip_to_list[i:i + 2] for i in range(0, len(ip_to_list), 2)]
        mac = "00"
        for octet in octets:
            mac = mac + ":{}{}".format(octet[0], octet[1])

        return mac

    def get_mac(self, ip):
        mac = "00:00:00:00:00:00"
        try:
            check_ip = ipaddress.ip_address(ip)
            valid_ip = check_ip.is_private
        except Exception as e:
            self.app.logger.error("get_mac(): not a valid ip address: %s", e)
        if valid_ip:
            found_mac = False
            for cmx in self.cmx_list:
                if cmx == 'test':
                    mac = self.ip_to_mac(check_ip)
                    self.app.logger.debug("get_mac(): test mode, created mac {} from ip {}".format(mac, ip))
                    found_mac = True
                else:
                    url_client_ip = self.url.format(cmx) + ip
                    try:
                        request = requests.get(url=url_client_ip, auth=HTTPBasicAuth(self.username, self.password), verify=False, timeout=self.timeout)
                        if request.status_code == 200:
                            try:
                                parsed = json.loads(request.text)
                            except json.JSONDecodeError as e:
                                self.app.logger.debug("get_mac(): CMX did not return valid JSON, decode error   {}".format(request.text))
                                parsed = ''
                            if len(parsed) > 0:
                                mac = C
                                found_mac = True
                                self.app.logger.debug("get_mac(): request to cmx returned mac {}".format(mac))
                            else:
                                self.app.logger.debug("get_mac(): request cmx ip {} returned no mac.".format(ip))
                        else:
                            self.app.logger.info("get_mac(): request failed, got status code {}.".format(request.status_code))
                    except requests.exceptions.RequestException as e:
                        self.app.logger.info("get_mac(): request to cmx failed: %s", e)
                if found_mac:
                    break
        else:
            self.app.logger.info("get_mac(): ip {} not private address or perhaps invalid format".format(ip))


        return mac

    def hash_mac(self, mac):
        mac = mac.replace(":","")
        mac_hash = hashlib.sha1()
        if len(self.hash) > 0:
            mac_hash.update((mac + self.hash).encode())
            mac_right4 = mac_hash.hexdigest()[-8:]
            mac_hash = "00:00:" + mac_right4[0:2] + ":" + mac_right4[2:4] + ":" + mac_right4[4:6] + ":" + mac_right4[6:8]
        else:
            self.app.logger.info("hash_mac(): hash {} is zero length, just returning mac as hash mac {}".format(self.hash, mac))
            mac_hash = mac

        return mac_hash