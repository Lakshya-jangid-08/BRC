import math
import mmap
import multiprocessing
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading

def round_up(value):
    return math.ceil(value * 10) / 10

def initialize_city_data():
    return [float('inf'), float('-inf'), 0.0, 0]

def process_lines(lines, shared_data, data_lock):
    local_data = defaultdict(initialize_city_data)
    
    for line in lines:
        if not line:
            continue
        
        semicolon_position = line.find(b';')
        if semicolon_position == -1:
            continue
        
        city = line[:semicolon_position]
        score_string = line[semicolon_position+1:]
        
        try:
            score = float(score_string)
        except ValueError:
            continue
        
        entry = local_data[city]
        entry[0] = min(entry[0], score)
        entry[1] = max(entry[1], score)
        entry[2] += score
        entry[3] += 1
    
    with data_lock:
        for city, stats in local_data.items():
            entry = shared_data[city]
            entry[0] = min(entry[0], stats[0])
            entry[1] = max(entry[1], stats[1])
            entry[2] += stats[2]
            entry[3] += stats[3]

def process_file_chunk(filename, start_offset, end_offset):
    shared_data = defaultdict(initialize_city_data)
    data_lock = threading.Lock()
    
    with open(filename, "rb") as file:
        memory_map = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        file_size = len(memory_map)
        
        if start_offset != 0:
            memory_map.seek(start_offset)
            if memory_map.read(1) != b'\n':
                while memory_map.tell() < file_size and memory_map.read(1) != b'\n':
                    pass
            start_offset = memory_map.tell()
        
        memory_map.seek(end_offset)
        if memory_map.read(1) != b'\n':
            while memory_map.tell() < file_size and memory_map.read(1) != b'\n':
                pass
            end_offset = memory_map.tell()
        
        chunk = memory_map[start_offset:end_offset]
        memory_map.close()
    
    lines = chunk.split(b'\n')
    
    num_threads = 4
    lines_per_thread = (len(lines) + num_threads - 1) // num_threads
    thread_arguments = []
    
    for i in range(num_threads):
        start = i * lines_per_thread
        end = start + lines_per_thread
        thread_arguments.append((lines[start:end], shared_data, data_lock))
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(lambda args: process_lines(*args), thread_arguments)
    
    return shared_data

def merge_city_data(data_list):
    final_data = defaultdict(initialize_city_data)
    for data in data_list:
        for city, stats in data.items():
            final_entry = final_data[city]
            final_entry[0] = min(final_entry[0], stats[0])
            final_entry[1] = max(final_entry[1], stats[1])
            final_entry[2] += stats[2]
            final_entry[3] += stats[3]
    return final_data

def main(input_filename="testcase.txt", output_filename="output.txt"):
    with open(input_filename, "rb") as file:
        memory_map = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
        file_size = len(memory_map)
        memory_map.close()
    
    num_processes = multiprocessing.cpu_count() * 2
    chunk_size = file_size // num_processes
    chunks = [(i * chunk_size, (i + 1) * chunk_size if i < num_processes - 1 else file_size)
              for i in range(num_processes)]
    
    with multiprocessing.Pool(num_processes) as pool:
        tasks = [(input_filename, start, end) for start, end in chunks]
        results = pool.starmap(process_file_chunk, tasks)
    
    final_data = merge_city_data(results)
    
    output_lines = []
    for city in sorted(final_data.keys()):
        min_score, max_score, total_score, count = final_data[city]
        average_score = round_up(total_score / count)
        output_lines.append(f"{city.decode()}={round_up(min_score):.1f}/{average_score:.1f}/{round_up(max_score):.1f}\n")
    
    with open(output_filename, "w") as file:
        file.writelines(output_lines)

if __name__ == "__main__":
    main()