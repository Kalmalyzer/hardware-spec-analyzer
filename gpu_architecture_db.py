import json
import pickle
import requests

GPU_ARCHITECTURE_DB_CACHE_BINARY_FILE="cache/gpu_architecture_db_cache.bin"
GPU_ARCHITECTURE_DB_CACHE_TEXT_FILE="cache/gpu_architecture_db_cache.txt"

class GPUArchitectureDB:
    def __init__(self):
        self.read_cache()

    def get(self, card_id):
        card_name = GPUArchitectureDB.id_to_name(card_id)
        found, gpu = self.cache.get(card_name)
        if not found:
            found, gpu = GPUArchitectureDB.fetch_from_server(card_name)
            if found:
                self.cache.add_card(card_name, gpu)
            else:
                self.cache.add_unknown(card_name)
            self.write_cache()
        return gpu

    def read_cache(self):
        try:
            with open(GPU_ARCHITECTURE_DB_CACHE_BINARY_FILE, 'rb') as gpu_architecture_db_cache_file:
                self.cache = pickle.load(gpu_architecture_db_cache_file)
                print(f"Read GPU architecture DB cache, {len(self.cache.cards)} cards & {len(self.cache.unknowns)} unknowns")
        except:
            self.cache = GPUArchitectureDBCache()

    def write_cache(self):
        with open(GPU_ARCHITECTURE_DB_CACHE_BINARY_FILE, 'wb') as gpu_architecture_db_cache_file:
            pickle.dump(self.cache, gpu_architecture_db_cache_file)
            print(f"Written GPU architecture DB cache, {len(self.cache.cards)} cards & {len(self.cache.unknowns)} unknowns")

        with open(GPU_ARCHITECTURE_DB_CACHE_TEXT_FILE, 'wt') as gpu_architecture_db_cache_file:
            gpu_architecture_db_cache_file.write("Cards:\n")
            for card_name, gpu_entry in self.cache.cards.items():
                gpu_architecture_db_cache_file.write(f"  {card_name}: {gpu_entry}\n")

            gpu_architecture_db_cache_file.write("Unknowns:\n")
            for unknown_card_name in self.cache.unknowns:
                gpu_architecture_db_cache_file.write(f"  {unknown_card_name}\n")

    @staticmethod
    def id_to_name(card_id):
        if card_id == 'NVIDIA GeForce RTX 2060':
            return 'RTX 2060 (Founders Edition)' # This should have been mapped to Reference, but there is no such in the DB. Founders Edition is close though
        elif card_id == 'NVIDIA GeForce RTX 2070':
            return 'RTX 2070 (Reference)'
        elif card_id == 'NVIDIA GeForce RTX 2080':
            return 'RTX 2080 (Reference)'
        elif card_id == 'NVIDIA GeForce RTX 2080 Ti':
            return 'RTX 2080 Ti (Reference)'
        else:
            return card_id.removeprefix('AMD Radeon ').removeprefix('NVIDIA GeForce ').replace('SUPER', 'Super')

    @staticmethod
    def name_to_id(name):
        if name == 'RTX 2060 (Founders Edition)':
            return 'NVIDIA GeForce RTX 2060'
        elif name == 'RTX 2070 (Reference)':
            return 'NVIDIA GeForce RTX 2070'
        elif name == 'RTX 2080 (Reference)':
            return 'NVIDIA GeForce RTX 2080'
        elif name == 'RTX 2080 Ti (Reference)':
            return 'NVIDIA GeForce RTX 2080 Ti'
        elif name.startswith('RX '):
            return f"AMD Radeon RX {name}"
        elif name.startswith('GTX '):
            return f"NVIDIA GeForce GTX {name}".replace("Super", "SUPER")
        elif name.startswith('RTX '):
            return f"NVIDIA GeForce RTX {name}".replace("Super", "SUPER")
        else:
            return name

    @staticmethod
    def fetch_from_server(gpu_name):

        # GraphQL query
        # This is intended to search for a single entry in the GPU DB
        # However, since the query is a substring search on GPU name, we ask for as many matches as we can (max 10 supported by the server)
        #   and do exact comparison later
        # We might need to do pagination in case there are more than 10 hits in the future, but the DB doesn't contain that many similar entries yet

        query = """
                {
                search(query:"{gpu_name}",type:CARD,first:10) {
                    edges {
                    node {
                        ... on Card {
                        name,
                        computeUnitCount,
                        aluCount,
                        singlePrecisionPerformance,
                        baseFrequency,
                        turboFrequency,
                        memoryBusWidth,
                        memoryFrequency,
                        memorySize,
                        memoryType,
                        releaseDate,
                        vendor,
                        asic { name }
                        }
                    }
                    }
                }
                }
            """.replace('{gpu_name}', gpu_name)

        response = requests.get(url="https://db.thegpu.guru/graphql", data=query, headers={'Content-Type': 'application/graphql'})

        if response.status_code == 200:
            response_structure = json.loads(response.content)
            for node in response_structure['data']['search']['edges']:

                inner_node = node['node']
                name = inner_node['name']

                if name == gpu_name:
                    return True, GPUArchitectureDBEntry(name=name,
                        compute_unit_count=int(inner_node['computeUnitCount']),
                        alu_count=int(inner_node['aluCount']),
                        single_precision_performance_tflops=float(inner_node['singlePrecisionPerformance']),
                        base_frequency_hz=int(inner_node['baseFrequency']),
                        turbo_frequency_hz=int(inner_node['turboFrequency']) if inner_node['turboFrequency'] != None else None,
                        memory_bus_width_bits=int(inner_node['memoryBusWidth']),
                        memory_frequency_hz=float(inner_node['memoryFrequency']),
                        memory_size_bytes=int(inner_node['memorySize']),
                        memory_type=inner_node['memoryType'],
                        release_date=inner_node['releaseDate'],
                        vendor=inner_node['vendor'],
                        asic_name=inner_node['asic']['name'])

        return False, None


class GPUArchitectureDBCache:
    def __init__(self):
        self.cards = dict()
        self.unknowns = set()

    def get(self, gpu_name):
        if gpu_name in self.unknowns:
            return True, None
        elif gpu_name in self.cards:
            return True, self.cards[gpu_name]
        else:
            return False, None

    def add_card(self, gpu_name, gpu):
        self.cards[gpu_name] = gpu

    def add_unknown(self, gpu_name):
        self.unknowns.add(gpu_name)

class GPUArchitectureDBEntry:
    def __init__(self, name, compute_unit_count, alu_count, single_precision_performance_tflops, base_frequency_hz, turbo_frequency_hz, memory_bus_width_bits, memory_frequency_hz, memory_size_bytes, memory_type, release_date, vendor, asic_name):
        self.name = name
        self.compute_unit_count = compute_unit_count
        self.alu_count = alu_count
        self.single_precision_performance_tflops = single_precision_performance_tflops
        self.base_frequency_hz = base_frequency_hz
        self.turbo_frequency_hz = turbo_frequency_hz
        self.memory_bus_width_bits = memory_bus_width_bits
        self.memory_frequency_hz = memory_frequency_hz
        self.memory_size_bytes = memory_size_bytes
        self.memory_type = memory_type
        self.release_date = release_date
        self.vendor = vendor
        self.asic_name = asic_name

    def __str__(self):
        return f"{self.name}, {self.compute_unit_count} CUs, {self.alu_count} ALUs, {self.single_precision_performance_tflops} SP TFLOPs,\
 base {self.base_frequency_hz} Hz / turbo {self.turbo_frequency_hz} Hz, {self.memory_bus_width_bits} bits, mem {self.memory_frequency_hz} Hz,\
 {self.memory_size_bytes} bytes, {self.memory_type} type, released on {self.release_date}, vendor {self.vendor}, ASIC {self.asic_name}"

    def describe(self):
        return f"Compute: {self.single_precision_performance_tflops} SP TFLOPs, VRAM: {round(self.memory_size_bytes / (1024 * 1024 * 1024), 2)} GB {self.memory_type}"

if __name__ == '__main__':
    gpu_db = GPUArchitectureDB()
