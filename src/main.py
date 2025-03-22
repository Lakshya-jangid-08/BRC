import math
import sys
import threading
from collections import defaultdict

def round_to_infinity(x, d=1):
    factor = 10 ** d
    return (math.ceil if x >= 0 else math.trunc)(x * factor) / factor

def process_chunk(lines, cs_lock, cs):
    local_cs = defaultdict(lambda: [float('inf'), float('-inf'), 0, 0])
    for line in lines:
        c, s = line.strip().split(";")
        s = float(s)
        stats = local_cs[c]
        stats[0] = min(stats[0], s)
        stats[1] = max(stats[1], s)
        stats[2] += s
        stats[3] += 1
    
    with cs_lock:
        for c, stats in local_cs.items():
            merged = cs[c]
            merged[0] = min(merged[0], stats[0])
            merged[1] = max(merged[1], stats[1])
            merged[2] += stats[2]
            merged[3] += stats[3]

def main(input_file_name="testcase.txt", output_file_name="output.txt"):
    with open(input_file_name, "r") as input_file:
        lines = input_file.readlines()
    
    num_threads = min(8, len(lines))
    chunk_size = max(1, len(lines) // num_threads)
    chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
    
    cs = defaultdict(lambda: [float('inf'), float('-inf'), 0, 0])
    cs_lock = threading.Lock()
    threads = []
    
    for chunk in chunks:
        thread = threading.Thread(target=process_chunk, args=(chunk, cs_lock, cs))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    with open(output_file_name, "w") as output_file:
        for c in sorted(cs.keys()):
            mini = round_to_infinity(cs[c][0])
            meani = round_to_infinity(cs[c][2] / cs[c][3])
            maxi = round_to_infinity(cs[c][1])
            output_file.write(f"{c}={mini:.1f}/{meani:.1f}/{maxi:.1f}\n")

if __name__ == "__main__":
    main()