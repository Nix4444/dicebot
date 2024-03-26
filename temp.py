from deposit_module.balance_dbhandler import balanceManager

balancedb = balanceManager('database.sqlite3')

print(balancedb.add_to_balance(6639580643,1000))
