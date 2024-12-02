import unittest, json, os
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from flask import Flask, jsonify


HOST, PORT = "localhost", 5000
STATS_FILE = 'user_statistics.txt'


#R6
def server_test(url, method=None, data=None):
    if not method:
        method = "POST" if data else "GET"
    if data:
        data = json.dumps(data).encode()
    headers = {"Content-type": "application/json; charset=UTF-8"} \
                if data else {}
    req = Request(url=url, data=data, headers=headers, method=method)

    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            return result, resp.getcode()  # return the response body and status code
    except HTTPError as e:
        return json.loads(e.read().decode()), e.code  # handle HTTP error and return the error msg


class TestProjectServer(unittest.TestCase):

    #user info
    def test_missing_user_info(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"", "password":""})
        self.assertEqual(status_code, 401)
        self.assertEqual(res_json, {"error": "user info error"})

    def test_missing_user_info_username(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"", "password":"1110-pw"})
        self.assertEqual(status_code, 401)
        self.assertEqual(res_json, {"error": "user info error"})

    def test_missing_user_info_password(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1110", "password":""})
        self.assertEqual(status_code, 401)
        self.assertEqual(res_json, {"error": "user info error"})

    def test_user_info(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1110", "password":"1110-pw"})
        self.assertEqual(status_code, 200)

    def test_invalid_user_info_1(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1111", "password":"1112-pw"})
        self.assertEqual(status_code, 401)
        self.assertEqual(res_json, {"error": "user info error"})

    def test_invalid_user_info_2(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"s1111", "password":"1111-pw"})
        self.assertEqual(status_code, 401)
        self.assertEqual(res_json, {"error": "user info error"})
    
    def test_invalid_user_info_3(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":1111, "password":"1111-pw"})
        self.assertEqual(status_code, 401)
        self.assertEqual(res_json, {"error": "user info error"})

    #pi
    def test_pi_missing_simulations(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw"})
        self.assertEqual(status_code, 400)
        self.assertEqual(res_json, {"error": "missing field simulations"})

    def test_pi_invalid_simulations(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":1})
        self.assertEqual(status_code, 400)
        self.assertEqual(res_json, {"error": "invalid field simulations"})

    def test_pi_invalid_concurrency_int(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100000000, "concurrency":9})
        self.assertEqual(status_code, 400)
        self.assertEqual(res_json, {"error": "invalid field concurrency"})

    def test_pi_invalid_concurrency_string(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100000000, "concurrency":"8"})
        self.assertEqual(status_code, 400)
        self.assertEqual(res_json, {"error": "invalid field concurrency"})

    def test_pi_missing_concurrency(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100})
        self.assertEqual(status_code, 200)
        concurrency = res_json.get("concurrency")
        self.assertEqual(concurrency, 1)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value >= 2 and pi_value <= 4)

    def test_pi_1(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100, "concurrency":1})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value >= 2 and pi_value <= 4)

    def test_pi_2(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100000, "concurrency":4})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value >= 3.10 and pi_value <= 3.20)

    def test_pi_3(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":10000000, "concurrency":8})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value >= 3.14 and pi_value <= 3.15)

    def test_pi_4(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100000000, "concurrency":8})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value >= 3.141 and pi_value <= 3.142)

    #pi execution_time
    def test_pi_execution_time(self):
        high_concurrency_res_json, high_concurrency_status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100000, "concurrency":8})
        self.assertEqual(high_concurrency_status_code, 200)
        high_concurrency_execution_time = high_concurrency_res_json.get("execution_time")

        low_concurrency_res_json, low_concurrency_status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100000, "concurrency":1})
        self.assertEqual(low_concurrency_status_code, 200)
        low_concurrency_execution_time = low_concurrency_res_json.get("execution_time")

        self.assertLessEqual(low_concurrency_execution_time, high_concurrency_execution_time) #high < low, low > high


    #legacy pi
    def test_legacy_pi_missing_protocol(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw"})
        self.assertEqual(status_code, 400)
        self.assertEqual(res_json, {"error": "missing field protocol"})

    def test_legacy_pi_invalid_protocol(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"xxx"})
        self.assertEqual(status_code, 400)
        self.assertEqual(res_json, {"error": "invalid field protocol"})

    def test_legacy_pi_invalid_concurrency_int(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"tcp", "concurrency": 0})
        self.assertEqual(status_code, 400)
        self.assertEqual(res_json, {"error": "invalid field concurrency"})

    def test_legacy_pi_invalid_concurrency_string(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"tcp", "concurrency": "1"})
        self.assertEqual(status_code, 400)
        self.assertEqual(res_json, {"error": "invalid field concurrency"})

    def test_legacy_pi_missing_concurrency(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"tcp"})
        self.assertEqual(status_code, 200)
        concurrency = res_json.get("concurrency")
        self.assertEqual(concurrency, 1)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value==0 or(pi_value >= 2 and pi_value <= 4))

    def test_legacy_pi_1_tcp(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"tcp", "concurrency":1})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value==0 or(pi_value >= 2 and pi_value <= 4))

    def test_legacy_pi_1_udp(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"udp", "concurrency":1})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value==0 or(pi_value >= 2 and pi_value <= 4))

    def test_legacy_pi_2_tcp(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"tcp", "concurrency":4})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value==0 or(pi_value >= 2.35 and pi_value <= 3.75))

    def test_legacy_pi_2_udp(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"udp", "concurrency":4})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value==0 or(pi_value >= 2.35 and pi_value <= 3.75))

    def test_legacy_pi_3_tcp(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"tcp", "concurrency":8})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value==0 or(pi_value >= 3 and pi_value <= 3.3))

    def test_legacy_pi_3_udp(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"udp", "concurrency":8})
        self.assertEqual(status_code, 200)
        pi_value = res_json.get("pi")
        self.assertTrue(pi_value==0 or(pi_value >= 3 and pi_value <= 3.3))

    #statistics
    def test_get_statistics(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1113", "password":"1113-pw"})
        self.assertEqual(status_code, 200)
        curr_stats = {}
        if os.path.exists(STATS_FILE):  #get current statustics from txt file
            with open(STATS_FILE, 'r') as f:
                for line in f:
                    username, count = line.strip().split()
                    curr_stats[username] = int(count)
        self.assertEqual(res_json, curr_stats)

    def test_add_statistics_pi(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100})
        self.assertEqual(status_code, 200)
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1113", "password":"1113-pw"})
        self.assertEqual(status_code, 200)
        curr_stats = {}
        if os.path.exists(STATS_FILE):  #get current statustics from txt file
            with open(STATS_FILE, 'r') as f:
                for line in f:
                    username, count = line.strip().split()
                    curr_stats[username] = int(count)
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/pi", "POST", {"username":"1111", "password":"1111-pw", "simulations":100})
        self.assertEqual(status_code, 200)
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1113", "password":"1113-pw"})
        self.assertEqual(status_code, 200)
        curr_stats["1111"] += 1
        curr_stats["1113"] += 1
        self.assertEqual(res_json.get("1111"), curr_stats["1111"])
        self.assertEqual(res_json.get("1113"), curr_stats["1113"])

    def test_add_statistics_legacy_pi(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"tcp"})
        self.assertEqual(status_code, 200)
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1113", "password":"1113-pw"})
        self.assertEqual(status_code, 200)
        curr_stats = {}
        if os.path.exists(STATS_FILE):  #get current statustics from txt file
            with open(STATS_FILE, 'r') as f:
                for line in f:
                    username, count = line.strip().split()
                    curr_stats[username] = int(count)
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/legacy_pi", "POST", {"username":"1112", "password":"1112-pw", "protocol":"tcp"})
        self.assertEqual(status_code, 200)
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1113", "password":"1113-pw"})
        self.assertEqual(status_code, 200)
        curr_stats["1112"] += 1
        curr_stats["1113"] += 1
        self.assertEqual(res_json.get("1112"), curr_stats["1112"])
        self.assertEqual(res_json.get("1113"), curr_stats["1113"])

    def test_add_statistics_statistics(self):
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1113", "password":"1113-pw"})
        self.assertEqual(status_code, 200)
        curr_stats = {}
        if os.path.exists(STATS_FILE):  #get current statustics from txt file
            with open(STATS_FILE, 'r') as f:
                for line in f:
                    username, count = line.strip().split()
                    curr_stats[username] = int(count)
        res_json, status_code = server_test(f"http://{HOST}:{PORT}/statistics", "POST", {"username":"1113", "password":"1113-pw"})
        self.assertEqual(status_code, 200)
        curr_stats["1113"] += 1
        self.assertEqual(res_json.get("1113"), curr_stats["1113"])

if __name__ == '__main__':
    unittest.main()