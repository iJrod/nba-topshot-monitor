import requests
import json
import pandas as pd
import time
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, HardwareType
from fp.fp import FreeProxy
import logging
from dhooks import Webhook, Embed
from datetime import datetime

logging_formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
def setup_logger(name, log_file, level=logging.INFO):
    """Function to allow multiple loggers"""

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(logging_formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# General logger
gLog = setup_logger('NBA_TOPSHOT_MONITOR', 'nba-topshot-monitor.log')


def get_stock(proxy, headers):
    packs = request_pack_stock(proxy, headers)

    df_data = packs['data']['searchPackListings']['data']['searchSummary']['data']['data']
    df = pd.DataFrame(df_data)
    #print(df)

    return df_data

def request_pack_stock(proxy, headers):
    """
    Makes a request to NBA Top Shot's GraphQL API endpoint.
    Return its content.
    """
    query = """
        query SearchPackListings($input: SearchPackListingsInput!) {
        searchPackListings(input: $input) {
            data {
            searchSummary {
                data {
                ... on PackListings {
                    data {
                    id
                    price
                    title
                    remaining
                    totalPackCount
                    expiryDate
                    preorder
                    images {
                        type
                        url
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
                __typename
                }
                __typename
            }
            __typename
            }
            __typename
        }
        }
    """
    variables = {'input': {'searchInput': {'pagination': {'cursor': "", 'direction': "RIGHT", 'limit': '100'}}}}

    url = 'https://api.nbatopshot.com/marketplace/graphql?SearchPackListings'
    r = requests.post(url, json={'query': query, 'variables': variables})
    packs = json.loads(r.text)
    #df_data = packs['data']['searchPackListings']['data']['searchSummary']['data']['data']
    #df = pd.DataFrame(df_data)
    return packs

def stock_processor(id, price, title, remaining, totalPackCount, preorder, start, proxy, headers):
    """
    Scrapes each pack on the store and checks whether the product is in-stock or not. If in-stock
    it will send a Discord notification
    """

    r = request_pack_stock(proxy, headers)
    packs = r['data']['searchPackListings']['data']['searchSummary']['data']['data']

    for pack in packs:
        item = [pack['id'], pack['title'], pack['price'], pack['remaining'], pack['totalPackCount'], pack['preorder']]
        #print(f'\n\nITEM:{item}\n\n')
        if pack['remaining'] == remaining: #change back to !=
            # Checks if it already exists in our instock
            if checker(item):
                pass
            else:
                # Add to instock dict
                INSTOCK.append(item)
                print(f'\n\nINSTOCK:{INSTOCK}\n\n')
                # Send a notification to the discord webhook with the in-stock product
                if start == 0:
                    print('Sending new Notification')
                    print(item)
                    discord_webhook(item)
                    logging.info(msg='Successfully sent Discord notification')

        else:
            if checker(item):
                INSTOCK.remove(item)

def discord_webhook(product_item):
    hook = Webhook(url="https://discord.com/api/webhooks/789656728189927424/5PXKFTs0zOcTB7ZwGrMjp0r-MrtD8Hr06UkeYbgVufJN68gIzsLb5J0uSf5v0pwAOB1l")
    """
    Sends a Discord webhook notification to the specified webhook URL
    :param product_item: An array of the product's details
    :return: None
    """
    embed = Embed(
        color=int(16711816)
    )
    if product_item == 'initial':
        embed.description = 'NBA Top Shot Monitor // INITIALISED // Twitter: @LNDNHYPE :smile:'
    else:
        embed.set_author('NBA Top Shot Monitor')
        embed.set_title(title=f'{product_item[1]}')  # Item Name
        embed.add_field(name='Price:', value=product_item[2], inline=True)
        embed.add_field(name='Stock Count:', value=product_item[4], inline=True)
        embed.add_field(name='Remaining:', value=product_item[3], inline=True)
        embed.add_field(name='Pre Order:', value=product_item[5], inline=False)
        #embed.set_thumbnail(product_item[4])

    embed.set_footer(text=f'Developer Twitter: @LNDNHYPE • {datetime.now().strftime("%Y-%m-%d %H:%M")}',icon_url='https://i.imgur.com/jjOXloc.png')

    try:
        hook.send(embed=embed)
    except requests.exceptions.HTTPError as err:
        print(err)
        logging.error(msg=err)
    else:
        print("Payload delivered successfully")
        logging.info("Payload delivered successfully")

def checker(product):
    """
    Determines whether the product status has changed
    :return: Boolean whether the status has changed or not
    """
    for item in INSTOCK:
        if item == product:
            return True
    return False

def monitor():
    """
    Initiates the monitor
    :return: None
    """
    print('STARTING MONITOR')
    gLog.info(msg='Successfully started monitor')
    discord_webhook('initial')
    start = 1
    proxy_no = 0

    proxy_list = "".split('%')
    proxy = {"http": f"http://{proxyObject.get()}"} if proxy_list[0] == "" else {"http": f"http://{proxy_list[proxy_no]}"}
    headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
    keywords = "".split('%')
    while True:
        try:
            packs = get_stock(proxy, headers)
            time.sleep(float(3))

            for pack in packs:
                check = False
                if keywords == "":
                    stock_processor(pack['id'], pack['price'], pack['title'], pack['remaining'], pack['totalPackCount'], pack['preorder'], start, proxy, headers)
                else:
                    for key in keywords:
                        if key.lower() in pack['title'].lower():
                            check = True
                            break
                    if check:
                        stock_processor(pack['id'],  pack['price'], pack['title'], pack['remaining'], pack['totalPackCount'], pack['preorder'], start, proxy, headers)
                time.sleep(0.5)
            start = 0
            gLog.info(msg='Successfully monitored site')
        except Exception as e:
            print(e)
            gLog.error(e)
            headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
            #if CONFIG['PROXY'] == "":
            if proxy_list == "":
                proxy = {"http": f"http://{proxyObject.get()}"}
            else:
                proxy_no = 0 if proxy_no == (len(proxy_list)-1) else proxy_no + 1
                proxy = {"http": f"http://{proxy_list[proxy_no]}"}


if __name__ == '__main__':
    INSTOCK = []
    software_names = [SoftwareName.CHROME.value]
    hardware_type = [HardwareType.MOBILE__PHONE]
    user_agent_rotator = UserAgent(software_names=software_names, hardware_type=hardware_type)  
    proxyObject = FreeProxy(country_id='GB', rand=True)
    monitor()