import csv
import io
import requests

STEAM_DB_CSV_URL="https://raw.githubusercontent.com/jdegene/steamHWsurvey/refs/heads/master/shs.csv"
STEAM_DB_DESIRED_DATE="2025-08-01"

STEAM_DB_TEXT_FILE="cache/steam_db.txt"

class SteamDB:
    def __init__(self):

        self.cards = dict()
        video_card_description = "Video Card Description"

        get_csv_request = requests.get(STEAM_DB_CSV_URL)
        if get_csv_request.status_code != 200:
            print(f"Error while fetching file {STEAM_DB_CSV_URL}, status code {get_csv_request.status_code}")
            raise Exception(f"Error fetching {STEAM_DB_CSV_URL}")

        reader = csv.reader(io.StringIO(get_csv_request.text, newline=''), delimiter=',', quotechar='"')
        for row in reader:
            if (row[0] == STEAM_DB_DESIRED_DATE) and (row[1] == video_card_description) and (row[2] != ""):
                name = row[2]
                popularity=float(row[4])
                self.cards[name]=SteamHWSurveyVideoCard(name=name, popularity=popularity)

        print(f"Read Steam DB, {len(self.cards)} entries")

        self.write_text()

    def get(self, card_id):
        return self.cards.get(card_id)

    def remove(self, card_id):
        card_to_remove = self.cards.get(card_id)
        if card_to_remove == None:
            raise f"Card {card_id} does not exist in steam DB"

        del self.cards[card_id]
        for card_id, card in self.cards.items():
            card.popularity = card.popularity * (1.0 / (1.0 - card_to_remove.popularity))

    def write_text(self):

        with open(STEAM_DB_TEXT_FILE, 'wt') as steam_db_text_file:
            for steam_name, steam_entry in self.cards.items():
                steam_db_text_file.write(f"{steam_name}: {steam_entry}\n")


    def iter(self):
        return self.cards.values()

class SteamHWSurveyVideoCard:
    def __init__(self, name, popularity):
        self.name = name
        self.popularity = popularity

    def __str__(self):
        return f"{self.name}, {self.popularity}"

if __name__ == '__main__':
    steam_db = SteamDB()
