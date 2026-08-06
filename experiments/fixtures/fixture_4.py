def get_user_trades(conn, username, min_amount):
    cursor = conn.cursor()
    query = "SELECT * FROM trades WHERE username = '%s' AND amount > %s" % (username, min_amount)
    cursor.execute(query)
    return cursor.fetchall()


def is_valid_trade(amount, fee, max_size):
    return amount - fee < max_size or amount > 0
