#!/usr/bin/env python3
"""
Log Analyzer – parses a server log, reports statistics, anomalies, and slowest endpoints.
Handles multiple timestamp formats, missing status codes, extra fields, JSON lines, and malformed entries.
"""

import re
import sys
import json
from collections import defaultdict, Counter
from datetime import datetime

# Timestamp parsers: try in order
TIMESTAMP_PATTERNS = [
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "%Y-%m-%dT%H:%M:%SZ"),
    (r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}", "%Y/%m/%d %H:%M:%S"),
    (r"\d{2}-\w{3}-\d{4} \d{2}:\d{2}:\d{2}", "%d-%b-%Y %H:%M:%S"),
    (r"\d{10}", "epoch"),  # 10-digit epoch seconds
]

def parse_timestamp(token: str):
    for pattern, fmt in TIMESTAMP_PATTERNS:
        if re.fullmatch(pattern, token):
            if fmt == "epoch":
                try:
                    return datetime.fromtimestamp(int(token))
                except (OSError, ValueError):
                    pass
            else:
                try:
                    return datetime.strptime(token, fmt)
                except ValueError:
                    continue
    return None

def parse_response_time(token: str):
    """Return time in milliseconds as float, or None."""
    if token.endswith("ms"):
        try:
            return float(token[:-2])
        except ValueError:
            pass
    elif token.endswith("s"):
        try:
            return float(token[:-1]) * 1000
        except ValueError:
            pass
    else:
        try:
            val = float(token)
            if val < 10000:   # assume raw ms if under 10 sec
                return val
            else:
                # could be seconds -> convert
                return val * 1000
        except ValueError:
            pass
    return None

def parse_line(line: str):
    """
    Try to parse a log line.
    Returns a dict with keys: timestamp, ip, method, path, status, response_time, extra, malformed
    Returns None if completely unparsable.
    """
    if not line.strip():
        return {"malformed": True}

    # Check for JSON line
    if line.strip().startswith("{"):
        try:
            data = json.loads(line)
            ts = parse_timestamp(data.get("timestamp", ""))
            rt = parse_response_time(str(data.get("response_time", "")))
            return {
                "timestamp": ts,
                "ip": data.get("ip"),
                "method": data.get("method"),
                "path": data.get("path"),
                "status": data.get("status"),
                "response_time": rt,
                "extra": "",
                "malformed": False
            }
        except json.JSONDecodeError:
            return {"malformed": True}

    # Split by whitespace (handles tabs / spaces)
    parts = line.strip().split()
    if len(parts) < 5:
        return {"malformed": True}  # need at least ts, ip, method, path, something

    ts = parse_timestamp(parts[0])
    if not ts:
        return {"malformed": True}

    ip = parts[1]
    method = parts[2]
    path = parts[3]
    status = None
    rt = None
    extra = ""

    # The next token could be status code or response time if status missing
    # We expect: ... method path [status] [response_time] [extra...]
    # Heuristic: if token 4 looks like a number with possible unit, it's response time,
    # else assume it's status code and token 5 is response time.
    idx = 4
    if idx < len(parts):
        token = parts[idx]
        if token == "-" or token.isdigit():
            # Could be status or missing status placeholder
            status_str = token
            if status_str != "-":
                status = int(status_str)
            else:
                status = None
            idx += 1
        # else: no status present, so token 4 is response time (handled below)

    if idx < len(parts):
        rt = parse_response_time(parts[idx])
        idx += 1

    if idx < len(parts):
        extra = " ".join(parts[idx:])

    return {
        "timestamp": ts,
        "ip": ip,
        "method": method,
        "path": path,
        "status": status,
        "response_time": rt,
        "extra": extra,
        "malformed": False
    }

def analyze_log(filepath):
    total_lines = 0
    malformed_count = 0
    parsed_lines = 0

    status_counts = Counter()
    method_counts = Counter()
    endpoint_hits = Counter()
    endpoint_times = defaultdict(list)  # for slowest calc
    ip_counts = Counter()
    anomalies = []  # store line numbers with problems

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            total_lines += 1
            parsed = parse_line(line)
            if parsed is None or parsed.get("malformed"):
                malformed_count += 1
                anomalies.append(lineno)
                continue

            parsed_lines += 1
            if parsed["status"] is not None:
                status_counts[parsed["status"]] += 1
            method_counts[parsed["method"]] += 1
            ep = parsed["method"] + " " + parsed["path"]
            endpoint_hits[ep] += 1
            if parsed["response_time"] is not None:
                endpoint_times[ep].append(parsed["response_time"])
            ip_counts[parsed["ip"]] += 1

    # Calculate slowest endpoints (average response time)
    slow_endpoints = []
    for ep, times in endpoint_times.items():
        if times:
            avg = sum(times) / len(times)
            max_time = max(times)
            slow_endpoints.append((avg, max_time, len(times), ep))
    slow_endpoints.sort(reverse=True)

    # Print summary
    print("=" * 60)
    print(f"LOG ANALYSIS REPORT")
    print("=" * 60)
    print(f"Total lines:      {total_lines}")
    print(f"Parsed OK:        {parsed_lines}")
    print(f"Malformed:        {malformed_count}")
    if malformed_count > 0:
        print(f"  (first 10 lines with issues: {anomalies[:10]})")

    print("\n--- Status Code Distribution ---")
    for code, cnt in status_counts.most_common():
        print(f"  {code}: {cnt}")

    print("\n--- HTTP Method Counts ---")
    for method, cnt in method_counts.items():
        print(f"  {method}: {cnt}")

    print("\n--- Top Requesters (IP) ---")
    for ip, cnt in ip_counts.most_common(5):
        print(f"  {ip}: {cnt}")

    print("\n--- Slowest Endpoints (avg ms, max ms, hits) ---")
    for avg, max_t, hits, ep in slow_endpoints[:10]:
        print(f"  {ep}: avg {avg:.1f}ms, max {max_t:.1f}ms, {hits} hits")

    print("=" * 60)

def main():
    if len(sys.argv) != 2:
        print("Usage: python log_analyzer.py <logfile>")
        sys.exit(1)
    analyze_log(sys.argv[1])

if __name__ == "__main__":
    main()