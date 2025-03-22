import math
import mmap
import multiprocessing
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
 
def round_up( value ):
    return math.ceil( value * 10 ) / 10

def initialize_city_data():
    return [math.inf, -math.inf, 0.0, 0]  

def process_sub_chunk(sub_chunk):
    city_data = defaultdict(initialize_city_data)
    for line in sub_chunk.split(b'\n'):
        if not line:
            continue
        semicolon_position = line.find(b';')
        if semicolon_position == -1:
            continue
        city = line[:semicolon_position]
        try:
            score = float(line[semicolon_position+1:])
        except ValueError:
            continue
        entry = city_data[city]
        entry[0] = min(entry[0], score)
        entry[1] = max(entry[1], score)
        entry[2] += score
        entry[3] += 1   
    return city_data

def process_file_chunk(filename, start_offset, end_offset):
    with open(filename, "rb") as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as memory_map:
            if start_offset != 0:
                while start_offset < len(memory_map) and memory_map[start_offset] != ord('\n'):
                    start_offset += 1
                start_offset += 1
            end = end_offset
            while end < len(memory_map) and memory_map[end] != ord('\n'):
                end += 1
            if end < len(memory_map):
                end += 1            
            chunk = memory_map[start_offset:end]
    sub_chunks = []
    previous = 0
    for _ in range(3):
        position = (len(chunk) * (_+1)) // 4
        while position < len(chunk) and chunk[position] != ord('\n'):
            position += 1
        sub_chunks.append(chunk[previous:position+1])
        previous = position+1
    sub_chunks.append(chunk[previous:])
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_sub_chunk, sub_chunks))
    merged_data = defaultdict(initialize_city_data)
    for result in results:
        for city, stats in result.items():
            entry = merged_data[city]
            entry[0] = min(entry[0], stats[0])
            entry[1] = max(entry[1], stats[1])
            entry[2] += stats[2]
            entry[3] += stats[3]
    return merged_data
def merge_city_data(data_list):
    final_data = defaultdict(initialize_city_data)
    for data in data_list:
        for city, stats in data.items():
            entry = final_data[city]
            entry[0] = min(entry[0], stats[0])
            entry[1] = max(entry[1], stats[1])
            entry[2] += stats[2]
            entry[3] += stats[3]
    return final_data
def main(input_filename="testcase.txt", output_filename="output.txt"):
    with open(input_filename, "rb") as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as memory_map:
            file_size = len(memory_map)
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