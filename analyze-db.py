import sqlite3
import pandas as pd

con = sqlite3.connect("test/example/.pathtraits.db")
df = pd.read_sql_query("SELECT * FROM data;", con)
df
