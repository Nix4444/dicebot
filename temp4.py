from deposit_module.balance_dbhandler import balanceManager
from dice_dbhandler import DiceManager
dicedata = DiceManager("database.sqlite3")
balacedb = balanceManager("database.sqlite3")
balacedb.add_to_balance(1005057106,1000)
