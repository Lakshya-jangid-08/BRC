import math
import mmap
import multiprocessing

def round_up(value):
    return math.ceil(value * 10) / 10

def process_file_chunk(filename, start_offset, end_offset):
    city_data = {}
    
    with open(filename, "rb") as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as memory_map:
            file_size = len(memory_map)
            
            if start_offset != 0:
                while start_offset < file_size and memory_map[start_offset] != ord('\n'):
                    start_offset += 1
                start_offset += 1
            
            end = end_offset
            while end < file_size and memory_map[end] != ord('\n'):
                end += 1
            if end < file_size:
                end += 1
            
            chunk = memory_map[start_offset:end]
    
    for line in chunk.splitlines():
        if not line:
            continue
        
        city, separator, score_string = line.partition(b';')
        if separator != b';':
            continue
        
        try:
            score = float(score_string)
        except ValueError:
            continue
        
        if city in city_data:
            stats = city_data[city]
            if score < stats[0]:
                stats[0] = score
            if score > stats[1]:
                stats[1] = score
            stats[2] += score
            stats[3] += 1
        else:
            city_data[city] = [score, score, score, 1]
    
    return city_data

def merge_city_data(data_list):
    final_data = {}
    for data in data_list:
        for city, stats in data.items():
            if city in final_data:
                final_stats = final_data[city]
                if stats[0] < final_stats[0]:
                    final_stats[0] = stats[0]
                if stats[1] > final_stats[1]:
                    final_stats[1] = stats[1]
                final_stats[2] += stats[2]
                final_stats[3] += stats[3]
            else:
                final_data[city] = stats.copy()
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
    for city in sorted(final_data.keys(), key=lambda c: c.decode()):
        min_score, max_score, total_score, count = final_data[city]
        average_score = round_up(total_score / count)
        output_lines.append(f"{city.decode()}={round_up(min_score):.1f}/{average_score:.1f}/{round_up(max_score):.1f}\n")
    
    with open(output_filename, "w") as file:
        file.writelines(output_lines)

if __name__ == "__main__":
    main()