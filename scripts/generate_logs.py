#!/usr/bin/env python3
"""Generate a sample server log file with various line formats and anomalies."""

import random
import sys
import os
from datetime import datetime, timedelta

IP_POOL = ["192.168.1.42", "10.0.0.7", "172.16.0.3", "8.8.8.8"]
METHODS = ["GET", "POST", "PUT", "DELETE"]
PATHS = ["/api/users", "/api/login", "/api/users/12", "/api/data"]
STATUSES = [200, 201, 301, 400, 401, 404, 500, "-"]
TIMESTAMP_FORMATS = {
    "iso": lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "slash": lambda d: d.strftime("%Y/%m/%d %H:%M:%S"),
    "apache": lambda d: d.strftime("%d-%b-%Y %H:%M:%S"),
    "epoch": lambda d: str(int(d.timestamp())),
}
RESPONSE_TIME_FORMATS = ["ms", "s", "raw"]

def random_timestamp():
    d = datetime(2024, 3, 15, 14, 23, 0) + timedelta(seconds=random.randint(0, 86400))
    return random.choice(list(TIMESTAMP_FORMATS.keys())), d

def random_response_time():
    ms = random.randint(10, 3000)
    fmt = random.choice(RESPONSE_TIME_FORMATS)
    if fmt == "ms":
        return f"{ms}ms"
    elif fmt == "s":
        return f"{ms/1000:.3f}s"
    else:
        return str(ms)   # raw milliseconds without unit

def generate_line(normal=True):
    if normal:
        fmt_name, ts = random_timestamp()
        ts_str = TIMESTAMP_FORMATS[fmt_name](ts)
        ip = random.choice(IP_POOL)
        method = random.choice(METHODS)
        path = random.choice(PATHS)
        status = random.choice(STATUSES)
        rt = random_response_time()
        return f"{ts_str} {ip} {method} {path} {status} {rt}"

    # Anomalous lines (5-10% of total)
    anomaly_type = random.choice([
        "extra_fields", "json_line", "missing_status", "garbage", "blank",
        "stacktrace", "different_delimiter"
    ])
    if anomaly_type == "extra_fields":
        base = generate_line(True)
        return base + ' "Mozilla/5.0" "https://example.com"'
    elif anomaly_type == "json_line":
        return '{"timestamp":"2024-03-15T15:00:00Z","ip":"10.0.0.1","method":"POST","path":"/api/action","status":200,"response_time":"45ms"}'
    elif anomaly_type == "missing_status":
        base = generate_line(True)
        parts = base.split()
        parts[4] = "-"
        return " ".join(parts)
    elif anomaly_type == "garbage":
        return "}{BAD LINE##!!"
    elif anomaly_type == "blank":
        return ""
    elif anomaly_type == "stacktrace":
        return "Traceback (most recent call last):\n  File \"app.py\", line 42, in <module>\nValueError: invalid"
    elif anomaly_type == "different_delimiter":
        # tab separated
        parts = generate_line(True).split()
        return "\t".join(parts)
    return ""

def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_logs.py <num_lines> <output_file>")
        sys.exit(1)

    num_lines = int(sys.argv[1])
    output_file = sys.argv[2]

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    with open(output_file, "w") as f:
        for _ in range(num_lines):
            if random.random() < 0.08:  # ~8% anomalies
                line = generate_line(normal=False)
            else:
                line = generate_line(normal=True)
            if line:
                f.write(line + "\n")
    print(f"Generated {num_lines} lines into {output_file}")

if __name__ == "__main__":
    main()