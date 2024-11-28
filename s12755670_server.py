import os, timeit, threading, socket
from flask import Flask, request, jsonify
from random import random
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

app = Flask(__name__)
HOST, PORT = "localhost", 5000
LEGACY_HOST, LEGACY_PORT = "0.0.0.0", 31416
STATS_FILE = 'user_statistics.txt'
lock = threading.Lock() 

#R1
def myth_value(n):
    count = 0
    for _ in range(n):
        x = random()
        y = random()
        if x * x + y * y < 1:
            count += 1
    return count

#R2
def is_float(n):    #check the string is/isnot valid float
    try:
        float(n)
        return True
    except ValueError:
        return False

def legacy_pi_tcp():
    global socket, LEGACY_HOST, LEGACY_PORT    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((LEGACY_HOST, LEGACY_PORT))
        pi = s.recv(1024)
    return pi.decode()

def legacy_pi_udp():
    global socket, LEGACY_HOST, LEGACY_PORT
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(b"", (LEGACY_HOST, LEGACY_PORT))
        pi, addr = s.recvfrom(1024)
    return pi.decode()

#R3, R5
def get_statistics():
    stats = {}
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            for line in f:
                username, count = line.strip().split()
                stats[username] = int(count)
    else:   #create file if have not file
        open(STATS_FILE, 'w').close()
    return stats

def save_statistics(stats):
    with open(STATS_FILE, 'w') as f:
        for username, count in stats.items():
            f.write(f"{username} {count}\n")

#R4
def is_valid_user(username, password):
    if not username or not isinstance(username, str) or len(username) != 4 or not username.isdigit():
        return False
    if not password or password != f"{username}-pw":
        return False
    return True

#R1
@app.post("/pi")
def pi():
    start_time = timeit.default_timer()
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    simulations = data.get("simulations")
    concurrency = data.get("concurrency", 1)

    #R4
    if not is_valid_user(username, password):
        return jsonify({"error": "user info error"}), 401
    #---

    if not simulations:
        return jsonify({"error": "missing field simulations"}), 400
    if simulations < 100 or simulations > 100000000:
        return jsonify({"error": "invalid field simulations"}), 400
    
    if not isinstance(concurrency, int) or concurrency < 1 or concurrency > 8:
        return jsonify({"error": "invalid field concurrency"}), 400
    

    total_count = 0
    if concurrency > 1:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            set = [executor.submit(myth_value, simulations // concurrency) for _ in range(concurrency)]
            total_count = sum(se.result() for se in set)
    else:
        total_count = myth_value(simulations)

    pi_estimate = total_count / simulations * 4
    end_time = timeit.default_timer()
    
    return jsonify({"simulations": simulations, "concurrency": concurrency, "pi": pi_estimate, "execution_time": end_time-start_time})
    
#R2
@app.post("/legacy_pi")
def legacy_pi():
    start_time = timeit.default_timer()
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    protocol = data.get("protocol")
    concurrency = data.get("concurrency", 1)

    #R4
    if not is_valid_user(username, password):
        return jsonify({"error": "user info error"}), 401
    #---

    if not protocol:
        return jsonify({"error": "missing field protocol"}), 400
    elif not isinstance(protocol, str) or (protocol not in ['tcp', 'udp']):
        return jsonify({"error": "invalid field protocol"}), 400
    
    if not isinstance(concurrency, int) or concurrency < 1 or concurrency > 8:
        return jsonify({"error": "invalid field concurrency"}), 400

    pi = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = []
        if protocol == "tcp": 
            pi_set = [executor.submit(legacy_pi_tcp) for _ in range(concurrency)]
        elif protocol == "udp": 
            pi_set = [executor.submit(legacy_pi_udp) for _ in range(concurrency)]
        
        for n in str(pi_set):
            if(is_float(n)):
                results.append(float(n))

        results_count = len(results)
        pi = sum(results) / results_count if results_count > 0 else 0

    end_time = timeit.default_timer()
    return jsonify({"protocol": protocol, "concurrency": concurrency, "num_valid_results": results_count, "pi": pi, "execution_time": end_time-start_time})

#R3
@app.post("/statistics")
def statistics():
    get_json = request.get_json()
    username = get_json.get("username")
    password = get_json.get("password")

    #R4
    if not is_valid_user(username, password):
        return jsonify({"error": "user info error"}), 401
    #---

    with lock:
        stats = get_statistics()

        if username in stats:
            stats[username] += 1
        else:
            stats[username] = 1
        save_statistics(stats)

    result = stats
    return jsonify(result)


if __name__ == "__main__":
    app.run()
    