from bit import Key

# Replace this with your private key in WIF format
private_key_in_WIF = 'KzDctM4vvxwb5oh8npckEyvs9ztascfNZcqqJiN1WR3H58mJ72vW'

# Initialize a Key object with your private key
key = Key(private_key_in_WIF)

# Output the address and its current balance
print(f"Address: {key.address}")
print(f"Balance: {key.get_balance('btc')} BTC")

# If you want to see the balance in Satoshi (the smallest unit of Bitcoin), you can do this:
print(f"Balance: {key.get_balance('satoshi')} satoshis")
