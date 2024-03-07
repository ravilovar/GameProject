import sqlite3


DB_NAME = 'data/game.sqlite'


# запись результата игрока в базу
def db_save_result(player, level, achieve):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute(f"INSERT INTO result(player, level, time) VALUES('{player}', {level}, '{achieve}')")
    con.commit()
    con.close()


# формирование списка с результатами игроков
def db_select_result():
    result = ['SPACE для выбора уровня',
              '-' * 48,
              '|       Игрок       |   Уровень   |    Время    |'
              ]
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    select_result = cur.execute("SELECT player, level, time as time FROM result").fetchall()
    for elem in select_result:
        elem_str = ''
        elem_str += f'| {str(elem[0]).ljust(16, " ")}  '
        elem_str += f'|  {str(elem[1]).ljust(2, " ")} уровень '
        elem_str += f'|  {str(elem[2]).ljust(8, " ")}   |'
        result.append(elem_str)
    result.append('-' * 48)
    con.close()
    return result
