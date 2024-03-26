from web3 import Web3
import requests,json
def usd_toeth(usd_amount):

    response = requests.get('https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD&api_key=addc799de5b1c06c6adb4381396de5d8711002a807a5521c1f85ffabe5ce146b')
    response = json.loads(response.text)
    eth_to_usd = response['USD']

    eth_amount = usd_amount * (1/eth_to_usd)
    eth_amount = round(eth_amount, 4)
    usd_2_fee = 2 * (1/eth_to_usd)
    usd_2_fee = round(usd_2_fee,4) #2 usd fee

    return eth_amount,usd_2_fee

def send_eth(recipient,value):
    try:
        eth_value,fee = usd_toeth(value)
        eth_value = eth_value - fee
        w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/229a95048da349249136c1d9b4af80c8'))
        private_key = ''
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
