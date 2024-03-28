from blockcypher import create_unsigned_tx
from litecoinutils.setup import setup
from litecoinutils.keys import P2pkhAddress, PrivateKey, PublicKey
from blockcypher import broadcast_signed_transaction
from blockcypher import make_tx_signatures
import requests,json
with open('config.json', 'r') as file:
        data = json.load(file)

CRYPTO_COMPARE_API = data['CRYPTO_COMPARE_API']
BLOCKCYPHER_API = data['BLOCKCYPHER_API']

def get_input_address(private_key):
    setup('mainnet')
    privkey = PrivateKey.from_wif(private_key)
    pub_key = privkey.get_public_key()
    publickey = pub_key.to_hex(compressed=True)
    address = pub_key.get_address(compressed=True).to_string()
    return address,publickey
LTC_PVT_KEY = "T8UynVrBuycH2fSkcAjPWv1B5w4N9tx2EEF58pFnGe8FTwbJLgJS"
def usd_to_ltc_to_litoshis(usd_amount):

    response = requests.get(f'https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD&api_key={CRYPTO_COMPARE_API}')
    response = json.loads(response.text)
    ltc_to_usd_rate = response['USD']

    ltc_amount = usd_amount * (1/ltc_to_usd_rate)
    ltc_amount = round(ltc_amount, 3)

    litoshis_amount = ltc_amount * 100000000

    return int(litoshis_amount)

def create_broadcast(output, value, privkey=LTC_PVT_KEY, apikey=BLOCKCYPHER_API):
    try:
        inputaddy, pubkey = get_input_address(privkey)
        inputs = [{'address': inputaddy}]
        outputs = [{'address': output, 'value': value}]
        unsigned_tx = create_unsigned_tx(inputs=inputs, outputs=outputs, coin_symbol='ltc', api_key=apikey)

        # Check if there are errors in the unsigned_tx and raise an exception if so
        if 'errors' in unsigned_tx:
            error_messages = '; '.join([error['error'] for error in unsigned_tx['errors']])
            raise Exception(f"Error creating unsigned transaction: {error_messages}")

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
    except Exception as e:
        return False
