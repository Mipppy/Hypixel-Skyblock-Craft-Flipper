from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import time, json, requests, datetime, webbrowser
from concurrent.futures import ThreadPoolExecutor

PLAYER_UUID = "0ec3a5dc1b4c446ebcf5b0b83551e768"
url = f'https://sky.coflnet.com/player/{PLAYER_UUID}'

options = Options()
driver = webdriver.Firefox(options=options)

try:
    driver.get(url)
    previous_height = 0
    current_height = driver.execute_script("return document.body.scrollHeight")
    n = 0
    while previous_height != current_height and n < 1000:
        n += 1
        previous_height = current_height
        driver.execute_script(f"window.scrollTo(0, {n * 2500});")
        time.sleep(1)
        current_height = driver.execute_script("return document.body.scrollHeight")

    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    player_details_div = soup.find('div', class_='PlayerDetailsList_list__LWKRB list-group')

    items_info = []

    def process_button(button):
        item_info = {}
        first_p = button.find('p')
        if first_p:
            p_text = first_p.get_text()
            if "Highest Bid:" in p_text:
                bid_value_str = p_text.split("Highest Bid: ")[1].split()[0].replace(",", "")
                bid_value = int(bid_value_str)
                item_info['highest_bid'] = bid_value

                img_src = button.find('img', class_='auctionItemImage')['src']
                if img_src.startswith('https://'):  
                    img_filename = img_src.split('/')[-1]
                    item_info['image_filename'] = img_filename

                    try:
                        response = requests.get(f"https://minionah.com/api/craftcost/{img_filename}")
                        if response.status_code == 200:
                            craft_cost = round(float(response.json().get(img_filename, 0)), 0)
                        else:
                            craft_cost = None  
                        item_info['crafting_cost'] = craft_cost
                    except Exception as e:
                        print(f"Error fetching crafting cost for {img_filename}: {e}")
                        item_info['crafting_cost'] = None

                    return item_info

    with ThreadPoolExecutor() as executor:
        results = executor.map(process_button, player_details_div.find_all('button', class_='list-group-item list-group-item-action'))

    items_info = [result for result in results if result is not None]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"data/items_info_{timestamp}.json"

    with open(filename, 'w') as file:
        json.dump(items_info, file, indent=4)

finally:
    driver.quit()
    webbrowser.open("./index.html", 0)
    
