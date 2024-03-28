from web3 import Web3
import requests,json

with open('config.json', 'r') as file:
        data = json.load(file)

CRYPTO_COMPARE_API = data['CRYPTO_COMPARE_API']
BLOCKCYPHER_API = data['BLOCKCYPHER_API']
INFURA_PROJECT_ID = data['INFURA_PROJECT_ID']

ETH_PVT_KEY = "NA"
def usd_toeth(usd_amount):

    response = requests.get(f'https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD&api_key={CRYPTO_COMPARE_API}')
    response = json.loads(response.text)
    eth_to_usd = response['USD']

    eth_amount = usd_amount * (1/eth_to_usd)
    eth_amount = round(eth_amount, 4)
    usd_2_fee = 2 * (1/eth_to_usd)
    usd_2_fee = round(usd_2_fee,4) #2 usd fee

    return eth_amount,usd_2_fee

def send_eth(recipient,value,pvt_key=ETH_PVT_KEY):
    try:
        eth_value,fee = usd_toeth(value)
        eth_value = eth_value - fee
        w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}'))
        private_key = pvt_key
        sender_address = w3.eth.account.from_key(private_key).address
        nonce = w3.eth.get_transaction_count(sender_address)
        value = w3.to_wei(eth_value, 'ether') # Sending 0.01 ETH
        gas = 21000 # Standard gas limit for ETH transfer
        gas_price = w3.to_wei('14', 'gwei')
        tx = {
        'nonce': nonce,
        'to': recipient,
        'value': value,
        'gas': gas,
        'gasPrice': gas_price
    }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash
    except ValueError:
        return False
