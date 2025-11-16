import psycopg2

def get_connection():
    return psycopg2.connect(
        host="myfitness.c1kosaucayij.eu-north-1.rds.amazonaws.com",
        database="myfitness",
        user="postgres",
        password="321Admin123!!"
    )