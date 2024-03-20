from ongoing_gamesdbhandler import OngoingGame
ongoing = OngoingGame('database.sqlite3')

a = ongoing.get_gameid_from_userid(5455454489)
print(a)
