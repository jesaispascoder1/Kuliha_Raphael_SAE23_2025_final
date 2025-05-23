import mysql.connector
import bcrypt
from random import choice
import csv


DB_CONFIG = {
    'host': "localhost",
    'user': "root",
    'password': "Tm!?-T:nBr6KY2j",
    'database': "sae23_kuliha",
    'charset': "utf8mb4",
    'use_unicode': True
}

def connect():
    return mysql.connector.connect(**DB_CONFIG)

### ==== UTILISATEUR ====
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def creer_utilisateur(nom, mdp):
    hashed_mdp = hash_password(mdp)
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Utilisateurs (Nom, Mot_de_passe) VALUES (%s, %s)",
            (nom, hashed_mdp)
        )
        conn.commit()
        return True
    except mysql.connector.Error as e:
        if "Duplicate" in str(e):
            return "duplicate"
        return str(e)
    finally:
        cur.close()
        conn.close()

def connexion_utilisateur(nom, mdp):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM Utilisateurs WHERE Nom=%s", (nom,))
        user = cur.fetchone()
        if user and check_password(user['Mot_de_passe'], mdp):
            cur.execute("UPDATE Utilisateurs SET Dernier_acces=NOW() WHERE ID=%s", (user['ID'],))
            conn.commit()
            return user
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_id(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)  # Pour accéder aux clés par nom
    try:
        cur.execute(
            "SELECT ID, Nom, Role, Dernier_acces FROM Utilisateurs WHERE ID = %s",
            (user_id,)
        )
        user = cur.fetchone()
        if user:
            # Ajoute une clé "is_admin" pour la logique de la webapp
            user['is_admin'] = (user['Role'] == "Admin")
            return user
        return None
    finally:
        cur.close()
        conn.close()

### ==== JEUX PUBLICS ====
def get_jeux_publiques():
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT j.ID, j.Titre, j.Description, j.Temps_moyen_termine,
                   pl.Nom AS Plateforme, 
                   g.Nom AS Genre, 
                   e.Nom AS Editeur,
                   u.Nom AS Ajoute_Par
            FROM Jeux j
            LEFT JOIN Plateformes pl ON j.Plateforme_ID=pl.ID
            LEFT JOIN Genres g ON j.Genre_ID=g.ID
            LEFT JOIN Editeurs e ON j.Editeur_ID=e.ID
            LEFT JOIN Utilisateurs u ON j.Ajoute_par=u.ID
            ORDER BY j.Titre COLLATE utf8mb4_unicode_ci ASC
        """)
        jeux = cur.fetchall()
        return jeux
    finally:
        cur.close()
        conn.close()

def get_or_create_id(table, nom):
    if not nom: return None
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT ID FROM {table} WHERE Nom = %s", (nom,))
        result = cur.fetchone()
        if result: return result[0]
        cur.execute(f"INSERT INTO {table} (Nom) VALUES (%s)", (nom,))
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()
        conn.close()

def suggerer_jeu_db(user_id, titre, description, temps, genre_nom, editeur_nom, plateforme_nom):
    conn = connect()
    try:
        genre_id = get_or_create_id('Genres', genre_nom) if genre_nom else None
        editeur_id = get_or_create_id('Editeurs', editeur_nom) if editeur_nom else None
        plateforme_id = get_or_create_id('Plateformes', plateforme_nom) if plateforme_nom else None
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO SuggestionsJeux
            (Titre, Description, Temps_moyen_termine, Genre_ID, Editeur_ID, Plateforme_ID, Suggere_par)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (titre, description, temps, genre_id, editeur_id, plateforme_id, user_id))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        return str(e)
    finally:
        conn.close()

### ==== JEUX PERSO ====
def get_noms_table(table):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT Nom FROM {table}")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

def get_liste_perso(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        # D'abord récupérer les jeux publics de la liste perso
        cur.execute("""
            SELECT lp.ID, lp.Utilisateur_ID, lp.Jeu_ID, lp.Ajoute_le, lp.Etat, lp.Note_personnelle,
                   j.Titre, j.Description, j.Temps_moyen_termine,
                   g.Nom AS Genre,
                   e.Nom AS Editeur,
                   p.Nom AS Plateforme
            FROM ListePerso lp
            LEFT JOIN Jeux j ON lp.Jeu_ID = j.ID
            LEFT JOIN Genres g ON j.Genre_ID = g.ID
            LEFT JOIN Editeurs e ON j.Editeur_ID = e.ID
            LEFT JOIN Plateformes p ON j.Plateforme_ID = p.ID
            WHERE lp.Utilisateur_ID = %s AND lp.Jeu_ID IS NOT NULL
            
            UNION ALL
            
            SELECT lp.ID, lp.Utilisateur_ID, lp.Jeu_ID, lp.Ajoute_le, lp.Etat, lp.Note_personnelle,
                   jpm.Titre, jpm.Description, NULL as Temps_moyen_termine,
                   jpm.Genre,
                   jpm.Editeur,
                   jpm.Plateforme
            FROM ListePerso lp
            JOIN JeuxPersoManuels jpm ON lp.ID = jpm.ListePerso_ID
            WHERE lp.Utilisateur_ID = %s AND lp.Jeu_ID IS NULL
            
            ORDER BY Titre COLLATE utf8mb4_unicode_ci ASC
        """, (user_id, user_id))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def ajouter_jeu_perso_public(user_id, jeu_id):
    conn = connect()
    cur = conn.cursor()
    try:
        # Vérifie si déjà dans la liste
        cur.execute(
            "SELECT 1 FROM ListePerso WHERE Utilisateur_ID=%s AND Jeu_ID=%s", 
            (user_id, jeu_id)
        )
        if cur.fetchone():
            return "Déjà dans votre liste perso."

        cur.execute(
            "INSERT INTO ListePerso (Utilisateur_ID, Jeu_ID, Etat) VALUES (%s, %s, %s)",
            (user_id, jeu_id, "Non commencé")
        )
        conn.commit()
        return True
    except Exception as e:
        return f"Erreur : {e}"
    finally:
        cur.close()
        conn.close()


def ajouter_jeu_perso_manuel(user_id, titre, description, genre, editeur, plateforme):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ListePerso (Utilisateur_ID, Jeu_ID, Etat)
            VALUES (%s, %s, %s)
        """, (user_id, None, "Non commencé"))
        listeperso_id = cur.lastrowid
        cur.execute("""
            INSERT INTO JeuxPersoManuels (ListePerso_ID, Titre, Description, Genre, Editeur, Plateforme)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (listeperso_id, titre, description, genre, editeur, plateforme))
        conn.commit()
        return True
    except Exception as e:
        return str(e)
    finally:
        cur.close()
        conn.close()

def supprimer_jeu_perso(user_id, item_id):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ListePerso WHERE ID=%s AND Utilisateur_ID=%s", (item_id, user_id))
        if cur.rowcount == 0:
            return "not_found"
        conn.commit()
        return True
    except Exception as e:
        return str(e)
    finally:
        cur.close()
        conn.close()

def changer_etat_jeu(user_id, item_id):
    conn = connect()
    cur = conn.cursor()
    try:
        # D'abord, récupérer l'état actuel
        cur.execute("SELECT Etat FROM ListePerso WHERE ID=%s AND Utilisateur_ID=%s", (item_id, user_id))
        result = cur.fetchone()
        if not result:
            return "not_found"
        
        etat_actuel = result[0]
        # Définir l'ordre de rotation des états
        etats = ["Non commencé", "En cours", "Terminé", "Abandonné"]
        # Trouver l'index actuel et calculer le prochain
        index_actuel = etats.index(etat_actuel)
        prochain_etat = etats[(index_actuel + 1) % len(etats)]
        
        # Mettre à jour avec le nouvel état
        cur.execute("UPDATE ListePerso SET Etat=%s WHERE ID=%s AND Utilisateur_ID=%s", 
                   (prochain_etat, item_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        return str(e)
    finally:
        cur.close()
        conn.close()

def stats_liste_perso(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        # Stats par état
        cur.execute("""
            SELECT Etat, COUNT(*) as nb
            FROM ListePerso
            WHERE Utilisateur_ID = %s AND Etat IS NOT NULL
            GROUP BY Etat
        """, (user_id,))
        stats_etats = {row['Etat']: row['nb'] for row in cur.fetchall()}

        # Stats des genres (jeux publics et manuels)
        cur.execute("""
            SELECT g.Nom as genre, COUNT(*) as count
            FROM ListePerso lp
            JOIN Jeux j ON lp.Jeu_ID = j.ID
            JOIN Genres g ON j.Genre_ID = g.ID
            WHERE lp.Utilisateur_ID = %s AND g.Nom IS NOT NULL AND g.Nom != ''
            GROUP BY g.Nom
            
            UNION ALL
            
            SELECT jpm.Genre as genre, COUNT(*) as count
            FROM ListePerso lp
            JOIN JeuxPersoManuels jpm ON lp.ID = jpm.ListePerso_ID
            WHERE lp.Utilisateur_ID = %s AND jpm.Genre IS NOT NULL AND jpm.Genre != ''
            GROUP BY jpm.Genre
            
            ORDER BY count DESC, genre ASC
        """, (user_id, user_id))
        
        genres_data = cur.fetchall()
        
        # Vérifier si l'utilisateur a des jeux
        cur.execute("""
            SELECT COUNT(*) as total
            FROM ListePerso
            WHERE Utilisateur_ID = %s
        """, (user_id,))
        total_jeux = cur.fetchone()['total']
        
        # Si aucun jeu, initialiser les états par défaut
        if total_jeux == 0:
            stats_etats = {
                "Non commencé": 0,
                "En cours": 0,
                "Terminé": 0,
                "Abandonné": 0
            }
        
        # Trouver le genre favori (celui avec le plus de jeux)
        genre_favori = genres_data[0]['genre'] if genres_data else "Aucun"
        
        return {
            "etats": stats_etats,
            "genres_data": genres_data,
            "genre_favori": genre_favori
        }
    except Exception as e:
        return {
            "etats": {
                "Non commencé": 0,
                "En cours": 0,
                "Terminé": 0,
                "Abandonné": 0
            },
            "genres_data": [],
            "genre_favori": "Aucun"
        }
    finally:
        cur.close()
        conn.close()

### ==== TIRAGE ====
def tirage_jeu_ma_liste(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        # Récupérer les jeux publics de la liste perso
        cur.execute("""
            SELECT j.ID, j.Titre, lp.ID as ListePerso_ID, lp.Etat,
                   j.Description, j.Temps_moyen_termine,
                   g.Nom AS Genre, e.Nom AS Editeur, p.Nom AS Plateforme
            FROM ListePerso lp
            JOIN Jeux j ON lp.Jeu_ID = j.ID
            LEFT JOIN Genres g ON j.Genre_ID = g.ID
            LEFT JOIN Editeurs e ON j.Editeur_ID = e.ID
            LEFT JOIN Plateformes p ON j.Plateforme_ID = p.ID
            WHERE lp.Utilisateur_ID=%s AND lp.Jeu_ID IS NOT NULL
        """, (user_id,))
        jeux_publiques = cur.fetchall()

        # Récupérer les jeux manuels
        cur.execute("""
            SELECT jpm.Titre, lp.ID as ListePerso_ID, lp.Etat,
                   jpm.Description, NULL as Temps_moyen_termine,
                   jpm.Genre, jpm.Editeur, jpm.Plateforme
            FROM ListePerso lp
            JOIN JeuxPersoManuels jpm ON lp.ID = jpm.ListePerso_ID
            WHERE lp.Utilisateur_ID=%s AND lp.Jeu_ID IS NULL
        """, (user_id,))
        jeux_manuels = cur.fetchall()

        jeux = list(jeux_publiques) + list(jeux_manuels)
        if not jeux:
            return None
        jeu = choice(jeux)
        return {
            'titre': jeu['Titre'],
            'description': jeu['Description'],
            'temps': jeu['Temps_moyen_termine'],
            'genre': jeu['Genre'],
            'editeur': jeu['Editeur'],
            'plateforme': jeu['Plateforme'],
            'etat': jeu['Etat'],
            'liste_perso_id': jeu['ListePerso_ID'],
            'from_liste_perso': True
        }
    finally:
        cur.close()
        conn.close()

def tirage_jeu_publique():
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT j.ID, j.Titre, j.Description, j.Temps_moyen_termine,
                   g.Nom AS Genre, e.Nom AS Editeur, p.Nom AS Plateforme
            FROM Jeux j
            LEFT JOIN Genres g ON j.Genre_ID = g.ID
            LEFT JOIN Editeurs e ON j.Editeur_ID = e.ID
            LEFT JOIN Plateformes p ON j.Plateforme_ID = p.ID
        """)
        jeux = cur.fetchall()
        if not jeux:
            return None
        jeu = choice(jeux)
        return {
            'id': jeu['ID'],
            'titre': jeu['Titre'],
            'description': jeu['Description'],
            'temps': jeu['Temps_moyen_termine'],
            'genre': jeu['Genre'],
            'editeur': jeu['Editeur'],
            'plateforme': jeu['Plateforme'],
            'from_liste_perso': False
        }
    finally:
        cur.close()
        conn.close()

### ==== PARTAGE ====
def partager_jeu(user_id, cible_pseudo, listeperso_id, message):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT ID FROM Utilisateurs WHERE Nom=%s", (cible_pseudo,))
        row = cur.fetchone()
        if not row:
            return False, "Aucun utilisateur avec ce pseudo."
        cible_id = row[0]
        cur.execute("""
            INSERT INTO PartagesJeux (De_Utilisateur_ID, Vers_Utilisateur_ID, ListePerso_ID, Message)
            VALUES (%s, %s, %s, %s)
        """, (user_id, cible_id, listeperso_id, message))
        conn.commit()
        return True, "Jeu partagé !"
    except Exception as e:
        return False, f"Erreur lors du partage : {e}"
    finally:
        cur.close()
        conn.close()

def get_jeux_partages_reçus(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT 
                pj.ID as partage_id,
                u.Nom AS expediteur,
                pj.Message,
                pj.Date_partage,
                lp.ID as liste_perso_id,
                COALESCE(j.Titre, jpm.Titre) as titre,
                COALESCE(j.Description, jpm.Description) as description,
                j.Temps_moyen_termine,
                COALESCE(g.Nom, jpm.Genre) as genre,
                COALESCE(e.Nom, jpm.Editeur) as editeur,
                COALESCE(p.Nom, jpm.Plateforme) as plateforme
            FROM PartagesJeux pj
            JOIN Utilisateurs u ON pj.De_Utilisateur_ID = u.ID
            JOIN ListePerso lp ON pj.ListePerso_ID = lp.ID
            LEFT JOIN Jeux j ON lp.Jeu_ID = j.ID
            LEFT JOIN JeuxPersoManuels jpm ON lp.ID = jpm.ListePerso_ID
            LEFT JOIN Genres g ON j.Genre_ID = g.ID
            LEFT JOIN Editeurs e ON j.Editeur_ID = e.ID
            LEFT JOIN Plateformes p ON j.Plateforme_ID = p.ID
            WHERE pj.Vers_Utilisateur_ID = %s
            ORDER BY pj.Date_partage DESC
        """, (user_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def supprimer_jeu_partage_recu(user_id, partage_id):
    conn = connect()
    cur = conn.cursor()
    try:
        # Vérifier que le partage existe et est bien destiné à l'utilisateur
        cur.execute("""
            SELECT 1 FROM PartagesJeux 
            WHERE ID = %s AND Vers_Utilisateur_ID = %s
        """, (partage_id, user_id))
        if not cur.fetchone():
            return False, "Ce partage n'existe pas ou ne vous est pas destiné."
        
        # Supprimer le partage
        cur.execute("DELETE FROM PartagesJeux WHERE ID = %s", (partage_id,))
        conn.commit()
        return True, "Partage supprimé avec succès"
    except Exception as e:
        return False, f"Erreur lors de la suppression : {str(e)}"
    finally:
        cur.close()
        conn.close()

### ==== ADMIN ====
def get_users():
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT ID, Nom, Role, Dernier_acces FROM Utilisateurs ORDER BY Nom")
        users = cur.fetchall()
        # Convertir les objets datetime en chaînes pour la sérialisation JSON
        for user in users:
            if user['Dernier_acces']:
                user['Dernier_acces'] = user['Dernier_acces'].strftime('%Y-%m-%d %H:%M:%S')
        return users
    except mysql.connector.Error as e:
        print(f"Erreur MySQL dans get_users: {str(e)}")
        return []
    except Exception as e:
        print(f"Erreur inattendue dans get_users: {str(e)}")
        return []
    finally:
        cur.close()
        conn.close()

def delete_user(current_admin_id, user_id):
    if str(user_id) == str(current_admin_id):
        return False, "Impossible de se supprimer soi-même !"
    conn = connect()
    try:
        cur = conn.cursor()
        # Réattribuer les jeux à l'admin actuel
        cur.execute("UPDATE Jeux SET Ajoute_par = %s WHERE Ajoute_par = %s", (current_admin_id, user_id))
        
        # Supprimer les partages
        cur.execute("DELETE FROM PartagesJeux WHERE De_Utilisateur_ID=%s OR Vers_Utilisateur_ID=%s", (user_id, user_id))
        
        # ListePerso et JeuxPersoManuels
        cur.execute("SELECT ID FROM ListePerso WHERE Utilisateur_ID=%s", (user_id,))
        ids = [r[0] for r in cur.fetchall()]
        if ids:
            format_strings = ','.join(['%s'] * len(ids))
            cur.execute("DELETE FROM JeuxPersoManuels WHERE ListePerso_ID IN (%s)" % format_strings, tuple(ids))
        cur.execute("DELETE FROM ListePerso WHERE Utilisateur_ID=%s", (user_id,))
        cur.execute("DELETE FROM SuggestionsJeux WHERE Suggere_par=%s", (user_id,))
        cur.execute("DELETE FROM Utilisateurs WHERE ID=%s", (user_id,))
        conn.commit()
        return True, "Utilisateur supprimé"
    finally:
        conn.close()

def set_user_admin(user_id):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE Utilisateurs SET Role='Admin' WHERE ID=%s", (user_id,))
        conn.commit()
        return True, "Utilisateur promu admin."
    finally:
        cur.close()
        conn.close()

### ==== SUGGESTIONS ADMIN ====
def get_all_suggestions():
    print("Début de get_all_suggestions()")
    try:
        conn = connect()
        cur = conn.cursor(dictionary=True)
        try:
            print("Exécution de la requête SQL...")
            cur.execute("""
                SELECT 
                    s.ID,
                    s.Titre,
                    s.Description,
                    s.Temps_moyen_termine,
                    s.Genre_ID,
                    s.Editeur_ID,
                    s.Plateforme_ID,
                    s.Suggere_par,
                    s.Date_suggestion,
                    u.Nom as User,
                    g.Nom as Genre,
                    e.Nom as Editeur,
                    p.Nom as Plateforme
                FROM SuggestionsJeux s
                LEFT JOIN Utilisateurs u ON s.Suggere_par = u.ID
                LEFT JOIN Genres g ON s.Genre_ID = g.ID
                LEFT JOIN Editeurs e ON s.Editeur_ID = e.ID
                LEFT JOIN Plateformes p ON s.Plateforme_ID = p.ID
                ORDER BY s.Date_suggestion DESC
            """)
            results = cur.fetchall()
            print(f"Nombre de suggestions trouvées : {len(results)}")
            return results
        except mysql.connector.Error as e:
            print(f"Erreur MySQL dans get_all_suggestions : {str(e)}")
            return []
        except Exception as e:
            print(f"Erreur inattendue dans get_all_suggestions : {str(e)}")
            return []
        finally:
            cur.close()
            conn.close()
            print("Fin de get_all_suggestions()")
    except mysql.connector.Error as e:
        print(f"Erreur de connexion MySQL dans get_all_suggestions : {str(e)}")
        return []
    except Exception as e:
        print(f"Erreur inattendue lors de la connexion dans get_all_suggestions : {str(e)}")
        return []

def delete_suggestion(suggest_id):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM SuggestionsJeux WHERE ID=%s", (suggest_id,))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()

def accepter_suggestion(suggest_id, titre, description, temps, genre_id, editeur_id, plateforme_id, suggere_par):
    conn = connect()
    cur = conn.cursor()
    try:
        # Ajouter à Jeux
        cur.execute("""
            INSERT INTO Jeux
              (Titre, Description, Temps_moyen_termine, Genre_ID, Editeur_ID, Plateforme_ID, Ajoute_par)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (titre, description, temps, genre_id, editeur_id, plateforme_id, suggere_par))
        # Supprimer suggestion
        cur.execute("DELETE FROM SuggestionsJeux WHERE ID=%s", (suggest_id,))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()

def get_suggestion(suggest_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM SuggestionsJeux WHERE ID=%s",(suggest_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

# Fonctions utilitaires pour dropdowns (Optionnel, sinon hardcode)
def get_all(table):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"SELECT ID, Nom FROM {table} ORDER BY Nom")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

### ==== ADMIN LISTE PUBLIQUE ====
def get_all_jeux():
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT j.ID, j.Titre, j.Description, g.Nom AS Genre, e.Nom AS Editeur, p.Nom AS Plateforme, j.Temps_moyen_termine
            FROM Jeux j
            LEFT JOIN Genres g ON j.Genre_ID = g.ID
            LEFT JOIN Editeurs e ON j.Editeur_ID = e.ID
            LEFT JOIN Plateformes p ON j.Plateforme_ID = p.ID
            ORDER BY j.Titre
        """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def ajouter_jeu(titre, description, temps, genre_id, editeur_id, plateforme_id, ajoute_par):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Jeux (Titre, Description, Temps_moyen_termine, Genre_ID, Editeur_ID, Plateforme_ID, Ajoute_par)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (titre, description, temps, genre_id, editeur_id, plateforme_id, ajoute_par))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()

def supprimer_jeu(jeu_id):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Jeux WHERE ID=%s", (jeu_id,))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()

def get_jeu(jeu_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT * FROM Jeux WHERE ID=%s
        """, (jeu_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

### ==== ÉTATS ET STYLES ====
def get_prochain_etat(etat_actuel):
    etats = ["Non commencé", "En cours", "Terminé", "Abandonné"]
    try:
        index_actuel = etats.index(etat_actuel)
        return etats[(index_actuel + 1) % len(etats)]
    except ValueError:
        return etats[0]

def get_couleur_etat(etat):
    return {
        "Non commencé": "#6c757d",  # Gris
        "En cours": "#007bff",      # Bleu
        "Terminé": "#28a745",       # Vert
        "Abandonné": "#dc3545"      # Rouge
    }.get(etat, "#6c757d")

def get_couleur_genre(genre):
    return {
        # Genres d'action
        "Action": "#ff6b6b",            # Rouge vif
        "Action-Adventure": "#ff8787",   # Rouge clair
        "Action-RPG": "#fa5252",        # Rouge foncé
        
        # Genres d'aventure et RPG
        "Aventure": "#4b5bff",          # Bleu vif
        "RPG": "#9b59b6",              # Violet
        "MMORPG": "#8c44ad",           # Violet foncé
        "rp": "#9b59b6",               # Même que RPG
        
        # Genres de combat et compétition
        "Fighting": "#e74c3c",          # Rouge intense
        "MOBA": "#e67e22",             # Orange
        "Battle Royale": "#d35400",    # Orange foncé
        
        # Genres de tir et survie
        "FPS": "#c0392b",              # Rouge bordeaux
        "Survival Horror": "#2c3e50",   # Bleu nuit
        
        # Genres de monde ouvert et sandbox
        "Open-World": "#27ae60",        # Vert forêt
        "Sandbox": "#16a085",           # Vert-bleu
        
        # Genres de réflexion et puzzle
        "Puzzle": "#3498db",           # Bleu ciel
        "Platformer": "#2980b9",       # Bleu océan
        "Arcade": "#34495e",           # Gris bleuté
        
        # Genres de simulation et sport
        "Simulation": "#f1c40f",        # Jaune
        "Sport": "#2ecc71"             # Vert
        
    }.get(genre, "#6c757d")            # Gris par défaut

def get_style_etat(etat):
    couleur = get_couleur_etat(etat)
    return f"""
        background: {couleur};
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.9em;
        display: inline-block;
    """

def get_style_genre(genre):
    couleur = get_couleur_genre(genre)
    return f"""
        background: {couleur};
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.9em;
        display: inline-block;
    """

def get_couleur_temps(temps):
    if not temps or temps == 0:
        return "#6c757d"  # Gris pour temps inconnu
    elif temps <= 5:
        return "#20c997"  # Vert-bleu - Très court
    elif temps <= 10:
        return "#00b894"  # Vert menthe - Court
    elif temps <= 20:
        return "#00cec9"  # Cyan - Moyen-court
    elif temps <= 40:
        return "#0984e3"  # Bleu - Moyen
    elif temps <= 60:
        return "#6c5ce7"  # Violet - Moyen-long
    elif temps <= 100:
        return "#a55eea"  # Violet clair - Long
    else:
        return "#8e44ad"  # Violet foncé - Très long

def get_categorie_temps(temps):
    if not temps or temps == 0:
        return "Durée inconnue"
    elif temps <= 5:
        return "Très court"
    elif temps <= 10:
        return "Court"
    elif temps <= 20:
        return "Moyen-court"
    elif temps <= 40:
        return "Moyen"
    elif temps <= 60:
        return "Moyen-long"
    elif temps <= 100:
        return "Long"
    else:
        return "Très long"

def get_style_temps(temps):
    couleur = get_couleur_temps(temps)
    return f"""
        background: {couleur};
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.9em;
        display: inline-block;
    """

def get_jeu_partage_info(liste_perso_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        # D'abord essayer de récupérer un jeu manuel
        cur.execute("""
            SELECT 
                lp.ID as ListePerso_ID,
                lp.Jeu_ID,
                jpm.Titre,
                jpm.Description,
                jpm.Genre,
                jpm.Editeur,
                jpm.Plateforme
            FROM ListePerso lp
            JOIN JeuxPersoManuels jpm ON lp.ID = jpm.ListePerso_ID
            WHERE lp.ID = %s
        """, (liste_perso_id,))
        
        result = cur.fetchone()
        if result:
            return result
            
        # Si pas de jeu manuel, essayer de récupérer un jeu public
        cur.execute("""
            SELECT 
                lp.ID as ListePerso_ID,
                lp.Jeu_ID,
                j.Titre,
                j.Description,
                g.Nom as Genre,
                e.Nom as Editeur,
                p.Nom as Plateforme
            FROM ListePerso lp
            JOIN Jeux j ON lp.Jeu_ID = j.ID
            LEFT JOIN Genres g ON j.Genre_ID = g.ID
            LEFT JOIN Editeurs e ON j.Editeur_ID = e.ID
            LEFT JOIN Plateformes p ON j.Plateforme_ID = p.ID
            WHERE lp.ID = %s
        """, (liste_perso_id,))
        
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def import_games_from_csv(csv_content, admin_id):
    """
    Importe des jeux depuis un contenu CSV.
    Format attendu: Titre,Description,Temps,Genre,Editeur,Plateforme
    """
    conn = connect()
    cur = conn.cursor()
    try:
        reader = csv.DictReader(csv_content.splitlines())
        imported = 0
        errors = []
        
        for row in reader:
            try:
                # Récupérer ou créer les IDs pour genre, editeur et plateforme
                genre_id = get_or_create_id('Genres', row['Genre']) if row['Genre'] else None
                editeur_id = get_or_create_id('Editeurs', row['Editeur']) if row['Editeur'] else None
                plateforme_id = get_or_create_id('Plateformes', row['Plateforme']) if row['Plateforme'] else None
                
                # Convertir le temps en entier
                temps = int(float(row['Temps'])) if row['Temps'] else 0
                
                # Insérer le jeu
                cur.execute("""
                    INSERT INTO Jeux (Titre, Description, Temps_moyen_termine, Genre_ID, Editeur_ID, Plateforme_ID, Ajoute_par)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['Titre'],
                    row['Description'],
                    temps,
                    genre_id,
                    editeur_id,
                    plateforme_id,
                    admin_id
                ))
                imported += 1
                
            except Exception as e:
                errors.append(f"Erreur pour {row['Titre']}: {str(e)}")
                continue
        
        conn.commit()
        return {
            "success": True,
            "imported": imported,
            "errors": errors
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur lors de l'import: {str(e)}"
        }
    finally:
        cur.close()
        conn.close()
