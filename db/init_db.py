import mysql.connector

DB_NAME = "sae23_kuliha"

def connecter(select_db=True):
    """
    Connexion à MySQL.
    Avec select_db=False: connexion sans base (pour pouvoir la créer après).
    Avec select_db=True: connexion à la BDD.
    """
    kwargs = dict(
        host="localhost",
        user="root",
        password="Tm!?-T:nBr6KY2j",
        charset="utf8mb4",
    )
    if select_db:
        kwargs['database'] = DB_NAME
    return mysql.connector.connect(**kwargs)

def creer_base_si_absente():
    conn = connecter(select_db=False)
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"Base '{DB_NAME}' vérifiée/créée.")
    finally:
        cursor.close()
        conn.close()

def initialiser_base():
    # Étape 1 : s'assurer que la BDD existe
    creer_base_si_absente()
    # Étape 2 : se connecter dessus et lancer le SQL
    conn = connecter(select_db=True)
    cursor = conn.cursor()
    try:
        with open('schema.sql', 'r', encoding='utf-8') as file:
            sql_script = file.read()
            # Optionnel : enlever les lignes spécifiques au dump comme /*!xxxxx etc. avant split
            statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().startswith("/*!")]
            for statement in statements:
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as e:
                    print("="*30)
                    print(f"Erreur SQL : {str(e)}")
                    print("Statement fautif :")
                    print(statement[:300] + ("..." if len(statement) > 300 else ""))
                    print("="*30)
        conn.commit()
        print("Base de données initialisée avec succès à partir de schema.sql.")
    except FileNotFoundError:
        print("Erreur : le fichier 'schema.sql' est introuvable.")
    except Exception as e:
        print(f"Erreur inattendue : {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    initialiser_base()
