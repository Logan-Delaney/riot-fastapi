import requests

def getChamp(champ_id):
    champions = requests.get("https://ddragon.leagueoflegends.com/cdn/15.3.1/data/en_US/champion.json").json()
    for champ in champions['data']:
        if champions['data'][champ]['key'] == champ_id:
            return champions['data'][champ]['name']
    return None

if __name__ == "__main__":
    test_champ_id = "266"  # Example champion ID
    champ_name = getChamp(test_champ_id)
    if champ_name:
        print(f"The champion with ID {test_champ_id} is {champ_name}.")
    else:
        print(f"No champion found with ID {test_champ_id}.")