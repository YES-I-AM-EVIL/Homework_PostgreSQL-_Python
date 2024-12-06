import psycopg2
from psycopg2 import sql

# Функция для создания структуры БД
def create_db(conn):
    with conn.cursor() as cur:
        # Создание таблицы clients
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL
        );
        """)

        # Создание таблицы phones
        cur.execute("""
        CREATE TABLE IF NOT EXISTS phones (
            phone_id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            phone_number VARCHAR(20) UNIQUE,
            FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE
        );
        """)
        conn.commit()

# Функция для добавления нового клиента
def add_client(conn, first_name, last_name, email, phones=None):
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO clients (first_name, last_name, email)
        VALUES (%s, %s, %s)
        RETURNING client_id;
        """, (first_name, last_name, email))
        client_id = cur.fetchone()[0]
        conn.commit()
        if phones:
            for phone in phones:
                add_phone(conn, client_id, phone)
        return client_id

# Функция для добавления телефона для существующего клиента
def add_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO phones (client_id, phone_number)
        VALUES (%s, %s);
        """, (client_id, phone))
        conn.commit()

# Функция для изменения данных о клиенте
def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    with conn.cursor() as cur:
        query = "UPDATE clients SET "
        params = []
        if first_name:
            query += "first_name = %s, "
            params.append(first_name)
        if last_name:
            query += "last_name = %s, "
            params.append(last_name)
        if email:
            query += "email = %s, "
            params.append(email)
        query = query.rstrip(", ") + " WHERE client_id = %s"
        params.append(client_id)
        cur.execute(query, params)
        conn.commit()
        if phones is not None:
            cur.execute("DELETE FROM phones WHERE client_id = %s", (client_id,))
            conn.commit()
            for phone in phones:
                add_phone(conn, client_id, phone)

# Функция для удаления телефона для существующего клиента
def delete_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute("""
        DELETE FROM phones
        WHERE client_id = %s AND phone_number = %s;
        """, (client_id, phone))
        conn.commit()

# Функция для удаления существующего клиента
def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute("""
        DELETE FROM clients
        WHERE client_id = %s;
        """, (client_id,))
        conn.commit()

# Функция для поиска клиента по его данным
def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    with conn.cursor() as cur:
        query = "SELECT * FROM clients WHERE "
        params = []
        if first_name:
            query += "first_name = %s AND "
            params.append(first_name)
        if last_name:
            query += "last_name = %s AND "
            params.append(last_name)
        if email:
            query += "email = %s AND "
            params.append(email)
        if phone:
            query += "client_id IN (SELECT client_id FROM phones WHERE phone_number = %s) AND "
            params.append(phone)
        query = query.rstrip(" AND ")
        cur.execute(query, params)
        results = cur.fetchall()
        return results

# Пример использования функций
if __name__ == "__main__":
    with psycopg2.connect(database="netology_db", user="postgres", password="qwerty") as conn:
        # Создание структуры БД
        create_db(conn)

        # Добавление нового клиента
        client_id = add_client(conn, "John", "Doe", "john.doe@example.com", ["123-456-7890", "098-765-4321"])
        print(f"Client added with ID: {client_id}")

        # Изменение данных о клиенте
        change_client(conn, client_id, last_name="Smith", phones=["123-456-7890"])

        # Удаление телефона для существующего клиента
        delete_phone(conn, client_id, "123-456-7890")

        # Поиск клиента по его данным
        clients = find_client(conn, email="john.doe@example.com")
        print("Found clients:", clients)

        # Удаление существующего клиента
        delete_client(conn, client_id)
        print(f"Client with ID {client_id} deleted")
