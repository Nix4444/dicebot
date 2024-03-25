from blockcypher import create_unsigned_tx
from litecoinutils.setup import setup
from litecoinutils.keys import P2pkhAddress, PrivateKey, PublicKey
from blockcypher import broadcast_signed_transaction
from blockcypher import make_tx_signatures
import requests,json
def get_input_address(private_key):
    setup('mainnet')
    privkey = PrivateKey.from_wif(private_key)
    pub_key = privkey.get_public_key()
    publickey = pub_key.to_hex(compressed=True)
    address = pub_key.get_address(compressed=True).to_string()
    return address,publickey

def usd_to_ltc_to_litoshis(usd_amount):
    
    response = requests.get('https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD&api_key=addc799de5b1c06c6adb4381396de5d8711002a807a5521c1f85ffabe5ce146b')
    response = json.loads(response.text)
    ltc_to_usd_rate = response['USD']

    ltc_amount = usd_amount * (1/ltc_to_usd_rate)
    ltc_amount = round(ltc_amount, 3)
   
    litoshis_amount = ltc_amount * 100000000

    return int(litoshis_amount)

def create_broadcast(output, value, privkey='', apikey='eb56febc793143d082ec451951874961'):
    try:
        inputaddy, pubkey = get_input_address(privkey)
        inputs = [{'address': inputaddy}]
        outputs = [{'address': output, 'value': value}]
        unsigned_tx = create_unsigned_tx(inputs=inputs, outputs=outputs, coin_symbol='ltc', api_key=apikey)
        
        # Initialize empty lists for private and public keys
        privkey_list = []
        pubkey_list = []
        
        # Determine the number of elements in 'tosign'
        num_of_tosign_elements = len(unsigned_tx['tosign'])
    
        
        # Append the private key and public key 'num_of_tosign_elements' times
        for _ in range(num_of_tosign_elements):
            privkey_list.append(privkey)
            pubkey_list.append(pubkey)
        
        tx_signatures = make_tx_signatures(txs_to_sign=unsigned_tx['tosign'], privkey_list=privkey_list, pubkey_list=pubkey_list)
        
        
        # Broadcast the signed transaction
        tx_data = broadcast_signed_transaction(unsigned_tx=unsigned_tx, signatures=tx_signatures, pubkeys=pubkey_list, api_key=apikey, coin_symbol='ltc')
        hash = tx_data['tx']['hash']
        return hash
    except AssertionError:
        return False


