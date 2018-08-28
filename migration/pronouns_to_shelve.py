import sqlite3
import shelve


def copy_pronouns_to_shelve(shelve_path, sqlite3_file_path):
    with shelve.open(shelve_path) as target:
        if "pronouns" not in target:
            target["pronouns"] = {}
        conn = sqlite3.connect(sqlite3_file_path)
        c = conn.cursor()

        c.execute("SELECT nick, pronouns FROM pronouns")

        for row in c.fetchall():
            target["pronouns"][row[0]] = row[1]
