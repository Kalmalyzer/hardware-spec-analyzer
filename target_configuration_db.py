import json

TARGET_CONFIGURATIONS_FILE="input/target_configurations.json"

class TargetConfigurationDB:
    def __init__(self):
        self.configs = TargetConfigurationDB.read_configs()

    @staticmethod
    def read_configs():
        with open(TARGET_CONFIGURATIONS_FILE, 'rt') as target_configurations_file:
            target_configurations = json.load(target_configurations_file)
            results = dict()
            for config_spec_name, config_spec in target_configurations.items():
                results[config_spec_name] = TargetConfiguration(config_spec_name, config_spec)
            return results

    def items(self):
        return self.configs.items()

class TargetConfiguration:
    def __init__(self, name, gpu_name):
        self.name = name
        self.gpu_name = gpu_name
        
    def __str__(self):
        return f"{self.name} - {self.gpu_name}"