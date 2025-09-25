import csv
from tabulate import tabulate

from gpu_architecture_db import GPUArchitectureDB, GPUArchitectureDBEntry
from gpu_benchmark_db import GPUBenchmarkDB, GPUBenchmarkDBEntry
from steam_db import SteamDB
from target_configuration_db import TargetConfigurationDB

TARGET_CONFIGURATIONS_FILE="output/target_configurations.csv"
ALL_CARDS_FILE="output/all_cards.csv"

class Card:
    def __init__(self, card_id, steam_card, gpu_architecture_db_card, gpu_benchmark_db_entry):
        self.card_id = card_id
        self.steam_card = steam_card
        self.gpu_architecture_db_card = gpu_architecture_db_card
        self.gpu_benchmark_db_entry = gpu_benchmark_db_entry
    
    def __str__(self):
        return f"{self.card_id}: Steam: [{self.steam_card}], GPUArchitectureDB: [{self.gpu_architecture_db_card}], GPU Benchmark DB: [{self.gpu_benchmark_db_entry}]"

def create_cards(steam_db, gpu_db, gpu_benchmark_db):
    results = dict()

    for steam_db_card in steam_db.iter():
        card_id = steam_db_card.name
        gpu_architecture_db_card = gpu_db.get(card_id)
        gpu_benchmark_db_card = gpu_benchmark_db.get(card_id)
        results[card_id] = Card(card_id=card_id, steam_card=steam_db_card, gpu_architecture_db_card=gpu_architecture_db_card, gpu_benchmark_db_entry=gpu_benchmark_db_card)

    for card_id, gpu_benchmark_db_card in gpu_benchmark_db.items():
        if not card_id in results:
            steam_db_card = steam_db.get(card_id)
            gpu_architecture_db_card = gpu_db.get(card_id)
            results[card_id] = Card(card_id=card_id, steam_card=steam_db_card, gpu_architecture_db_card=gpu_architecture_db_card, gpu_benchmark_db_entry=gpu_benchmark_db_card)

    return results

def filter_cards_by_g3d_mark(target_card, cards):
    return {card_id: card for (card_id, card) in cards.items() if (card.gpu_benchmark_db_entry != None) and (card.gpu_benchmark_db_entry.g3d_mark >= target_card.gpu_benchmark_db_entry.g3d_mark)}

def get_eligible_cards(target_configuration, cards):
    target_card = cards.get(target_configuration.gpu_name)
    if target_card == None:
        raise f"Unable to find target GPU {target_configuration.gpu_name} among cards"

    eligible_cards = filter_cards_by_g3d_mark(target_card, cards)
    return eligible_cards

def calculate_market_share(cards):
    return sum(card.steam_card.popularity for card in cards.values() if card.steam_card != None)

class CardAnalysis:
    def __init__(self, eligible_cards, market_share):
        self.eligible_cards = eligible_cards
        self.market_share = market_share

    def __str__(self):
        return f"Cards: [{card.name for card in self.eligible_cards.keys()}] Market share: {self.market_share:.2f}"

def analyze(target_configuration_db, cards):

    results = dict()
    for target_configuration_name, target_configuration in target_configuration_db.items():

        try:
            eligible_cards = get_eligible_cards(target_configuration, cards)
            market_share = calculate_market_share(eligible_cards)
            results[target_configuration.gpu_name] = CardAnalysis(eligible_cards=eligible_cards, market_share=market_share)
        except:
            pass

    return results

#####################

def write_target_configurations_csv(target_configuration_db, cards, analyzed_cards):
    results = []
    for target_configuration_name, target_configuration in target_configuration_db.items():

        card = cards.get(target_configuration.gpu_name)
        if card != None:
            analyzed_card = analyzed_cards.get(target_configuration.gpu_name)
            market_share = f"{analyzed_card.market_share * 100:.2f}%"
            g3d_mark = card.gpu_benchmark_db_entry.g3d_mark if card.gpu_benchmark_db_entry != None else None
            gpu_description = card.gpu_architecture_db_card.describe() if card.gpu_architecture_db_card != None else None
            results.append([target_configuration.name, target_configuration.gpu_name, gpu_description, market_share, g3d_mark])
        else:
            results.append([target_configuration.name, target_configuration.gpu_name, None, None, None])

    with open(TARGET_CONFIGURATIONS_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Configuration", "GPU Name", "GPU description", "Market coverage", "G3D mark (performance metric)"])
        for line in results:
            writer.writerow(line)

    print(f"Results written to {TARGET_CONFIGURATIONS_FILE}")

    with open(TARGET_CONFIGURATIONS_FILE, 'rt') as csvfile:
        print(tabulate(csv.reader(csvfile), headers="firstrow", tablefmt='fancy_grid'))

def write_all_cards_csv(target_configuration_db, cards, analyzed_cards):

    sorted_target_configuration_names = sorted(target_configuration_db.configs.keys())

    results = []
    for card_id, card in cards.items():
        g3d_mark = card.gpu_benchmark_db_entry.g3d_mark if card.gpu_benchmark_db_entry != None else None
        gpu_description = card.gpu_architecture_db_card.describe() if card.gpu_architecture_db_card != None else None
        popularity = f"{card.steam_card.popularity * 100:.2f}%" if card.steam_card != None else None
        column_results = [card_id, gpu_description, popularity, g3d_mark]

        for target_configuration_name in sorted_target_configuration_names:
            target_configuration = target_configuration_db.configs.get(target_configuration_name)
            analyzed_card = analyzed_cards.get(target_configuration.gpu_name)
            included = "Yes" if analyzed_card != None and card_id in analyzed_card.eligible_cards else "No"
            column_results.append(included)

        results.append(column_results)

    results = sorted(results, key=lambda column: float(column[3]) if column[3] != None else 0, reverse=True)

    header_results = ["Configuration", "GPU Description", "Popularity", "G3D mark (performance metric)"]
    for target_configuration_name in sorted_target_configuration_names:
        header_results.append(target_configuration_name)

    results.insert(0, header_results)

    with open(ALL_CARDS_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for line in results:
            writer.writerow(line)

    print(f"Results written to {ALL_CARDS_FILE}")

    with open(ALL_CARDS_FILE, 'rt') as csvfile:
        print(tabulate(csv.reader(csvfile), headers="firstrow", tablefmt='fancy_grid'))

if __name__ == '__main__':
    print("Initializing SteamDB")
    steam_db = SteamDB()
    print("Initializing GPUArchitectureDB")
    gpu_db = GPUArchitectureDB()
    print("Initializing GPUBenchmarkDB")
    gpu_benchmark_db = GPUBenchmarkDB()
    print("Initializing TargetConfigurationDB")
    target_configuration_db = TargetConfigurationDB()
    print("All DBs up")

    # The "Other" category is about 10%
    # Remove it so it doesn't skew statistics when we calculate market share
    steam_db.remove("Other")

    cards = create_cards(steam_db, gpu_db, gpu_benchmark_db)
    analyzed_cards = analyze(target_configuration_db, cards)

    write_target_configurations_csv(target_configuration_db, cards, analyzed_cards)
    write_all_cards_csv(target_configuration_db, cards, analyzed_cards)
