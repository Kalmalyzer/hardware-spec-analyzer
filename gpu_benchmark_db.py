import pickle
import requests
import time

from selenium import webdriver 
from selenium.webdriver import Chrome 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.select import Select

GPU_ARCHITECTURE_DB_CACHE_BINARY_FILE="cache/gpu_benchmark_db_cache.bin"
GPU_ARCHITECTURE_DB_CACHE_TEXT_FILE="cache/gpu_benchmark_db_cache.txt"

def localized_number_to_integer(localized_number):
    return int(localized_number.replace(",", ""))

class GPUBenchmarkDBEntry:
    def __init__(self, name, g3d_mark, g2d_mark):
        self.name = name
        self.g3d_mark = g3d_mark
        self.g2d_mark = g2d_mark

    def __str__(self):
        return f"{self.name}: G3D mark {self.g3d_mark}, G2D mark {self.g2d_mark}"

    @staticmethod
    def id_to_name(card_id):
        return card_id.replace('NVIDIA GeForce ', 'GeForce ').replace('AMD Radeon ', 'Radeon ').replace('Intel HD Graphics ', 'Intel HD ')

    @staticmethod
    def name_to_id(name):
        if name.startswith('GeForce '):
            return f"NVIDIA {name}"
        if name.startswith('Radeon '):
            return f"AMD {name}"
        if name.startswith('Intel HD ') and not name.startswith('Intel HD Graphics '):
            return name.replace('Intel HD ', 'Intel HD Graphics ')
        return name

class GPUBenchmarkDB:
    def __init__(self):
        self.read_cache()

    def get(self, card_id):
        return self.cache.get(card_id)

    def read_cache(self):
        try:
            with open(GPU_ARCHITECTURE_DB_CACHE_BINARY_FILE, 'rb') as gpu_benchmark_db_cache_file:
                self.cache = pickle.load(gpu_benchmark_db_cache_file)
                print(f"Read GPU Benchmark DB cache, {len(self.cache.entries)} entries")
        except:
            self.cache = GPUBenchmarkDB.fetch_from_server()
            self.write_cache()

    def write_cache(self):
        with open(GPU_ARCHITECTURE_DB_CACHE_BINARY_FILE, 'wb') as gpu_benchmark_db_cache_file:
            pickle.dump(self.cache, gpu_benchmark_db_cache_file)
            print(f"Written GPU Benchmark DB cache, {len(self.cache.entries)} entries")

        with open(GPU_ARCHITECTURE_DB_CACHE_TEXT_FILE, 'wt') as gpu_benchmark_db_cache_file:
            for card_id, gpu_entry in self.cache.entries.items():
                gpu_benchmark_db_cache_file.write(f"{card_id}: {gpu_entry}\n")

    def items(self):
        return self.cache.entries.items()

    @staticmethod
    def fetch_from_server():

        # Define the Chrome webdriver options
        options = webdriver.ChromeOptions() 
        options.add_argument("--headless") # Set the Chrome webdriver to run in headless mode for scalability

        # By default, Selenium waits for all resources to download before taking actions.
        # However, we don't need it as the page is populated with dynamically generated JavaScript code.
        options.page_load_strategy = "none"

        # Pass the defined options objects to initialize the web driver 
        driver = Chrome(options=options) 
        # Set an implicit wait of 5 seconds to allow time for elements to appear before throwing an exception
        driver.implicitly_wait(5)

        url = "https://www.videocardbenchmark.net/GPU_mega_page.html"
        
        driver.get(url) 
        time.sleep(5)

        # Click "all" in the dropdown
        select_element = driver.find_element(By.NAME, 'cputable_length')
        select = Select(select_element)
        select.select_by_visible_text('All')

        # Extract results
        cpu_table = driver.find_element(By.ID, "cputable")
        cpu_table_rows = cpu_table.find_elements(By.XPATH, "//tbody/tr")

        results = dict()

        for cpu_table_row in cpu_table_rows:
            columns = cpu_table_row.find_elements(By.TAG_NAME, "td")
            gpu_name = columns[1].text
            g3d_mark = localized_number_to_integer(columns[2].text)
            g2d_mark = localized_number_to_integer(columns[3].text)

            card_id = GPUBenchmarkDBEntry.name_to_id(gpu_name)
            results[card_id] = GPUBenchmarkDBEntry(gpu_name, g3d_mark, g2d_mark)

        return GPUBenchmarkDBCache(results)


class GPUBenchmarkDBCache:
    def __init__(self, entries):
        self.entries = entries

    def get(self, card_id):
        return self.entries.get(card_id)

if __name__ == '__main__':
    gpu_benchmark_db = GPUBenchmarkDB()
    
