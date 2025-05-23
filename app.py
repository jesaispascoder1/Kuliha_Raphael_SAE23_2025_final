import cherrypy
from jinja2 import Environment, FileSystemLoader
import json
from random import choice
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Configuration pour utilisation sans interface graphique
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os
from db.models import (
    # Authentification et gestion utilisateurs
    creer_utilisateur, connexion_utilisateur, get_user_by_id, get_users,
    delete_user, set_user_admin,
    
    # Gestion des jeux publics
    get_jeux_publiques, get_all_jeux, ajouter_jeu, supprimer_jeu,
    
    # Gestion des suggestions
    suggerer_jeu_db, get_all_suggestions, delete_suggestion,
    accepter_suggestion, get_suggestion,
    
    # Gestion de la liste personnelle
    get_liste_perso, ajouter_jeu_perso_public, ajouter_jeu_perso_manuel,
    supprimer_jeu_perso, changer_etat_jeu, stats_liste_perso,
    
    # Fonctions de tirage
    tirage_jeu_ma_liste, tirage_jeu_publique,
    
    # Gestion des partages
    partager_jeu, get_jeux_partages_reçus, supprimer_jeu_partage_recu,
    get_jeu_partage_info,
    
    # Styles et états
    get_prochain_etat, get_style_etat, get_style_genre,
    get_couleur_etat, get_style_temps, get_categorie_temps,
    
    # Utilitaires
    get_or_create_id, import_games_from_csv
)

env = Environment(loader=FileSystemLoader('templates'))

class MonApp:

    @cherrypy.expose
    def index(self):
        user_id = cherrypy.session.get("user_id")
        user = get_user_by_id(user_id) if user_id else None
        jeux = get_jeux_publiques()

        # Préparer les données pour le template
        template = env.get_template('index.html')
        return template.render(
            title="Le_Backlog",
            jeux=jeux,
            user=user,
            user_connecte="true" if user else "false",
            admin_link=f"<a href='/admin'>Admin</a>" if user and user.get('is_admin') else "",
            ma_liste_link="<a href='/mes-jeux'>Ma liste</a>" if user else "",
            login_actions=(
                "<button class='btn-login' onclick='openPopup(false)'>Connexion</button> "
                "<button class='btn-register' onclick='openPopup(true)'>Créer un compte</button>"
            ) if not user else (
                f"<span class='user-info'>{user['Nom']}</span> "
                "<a href='/logout' class='btn'>Déconnexion</a>"
            ),
            get_style_genre=get_style_genre,
            get_style_temps=get_style_temps,
            get_categorie_temps=get_categorie_temps
        )

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def login_ajax(self):
        data = cherrypy.request.json
        user = connexion_utilisateur(data['nom'], data['mdp'])
        if user:
            cherrypy.session['user_id'] = user['ID']
            cherrypy.session['user_nom'] = user['Nom']
            return {"success": True}
        else:
            return {"success": False, "error": "Identifiants incorrects."}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def register_ajax(self):
        data = cherrypy.request.json
        ret = creer_utilisateur(data['nom'], data['mdp'])
        if ret is True:
            # après inscription, on connecte direct
            user = connexion_utilisateur(data['nom'], data['mdp'])
            cherrypy.session['user_id'] = user['ID']
            cherrypy.session['user_nom'] = user['Nom']
            return {"success": True}
        elif ret == "duplicate":
            return {"success": False, "error": "Nom déjà pris."}
        else:
            return {"success": False, "error": "Erreur: " + str(ret)}

    @cherrypy.expose
    def logout(self):
        cherrypy.session.pop("user_id", None)
        cherrypy.session.pop("user_nom", None)
        raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def ajouter_jeu_depuis_publique(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        data = cherrypy.request.json
        jeu_id = data.get("jeu_id")
        # À toi d'adapter la fonction suivante selon tes modèles
        res = ajouter_jeu_perso_public(user_id, jeu_id)
        if res is True:
            return {"success": True}
        else:
            return {"success": False, "error": str(res)}
        
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def sugg_jeu_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté."}
        d = cherrypy.request.json
        titre = d.get('titre', '').strip()
        if not titre:
            return {"success": False, "error": "Titre obligatoire"}
        description = d.get('description', '').strip()
        temps = int(d.get('temps') or 0)
        genre_nom = d.get('genre', '').strip()
        editeur_nom = d.get('editeur', '').strip()
        plateforme_nom = d.get('plateforme', '').strip()
        res = suggerer_jeu_db(user_id, titre, description, temps, genre_nom, editeur_nom, plateforme_nom)
        if res is True:
            return {"success": True}
        else:
            return {"success": False, "error": str(res)}

    def get_prochain_etat(self, etat_actuel):
        etats = ["Non commencé", "En cours", "Terminé", "Abandonné"]
        try:
            index_actuel = etats.index(etat_actuel)
            return etats[(index_actuel + 1) % len(etats)]
        except ValueError:
            return etats[0]

    @cherrypy.expose
    def mes_jeux(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            raise cherrypy.HTTPRedirect("/")
        
        user = get_user_by_id(user_id)
        jeux = get_liste_perso(user_id)

        # Génère la liste des jeux
        jeux_html = ""
        if jeux:
            for j in jeux:
                note = j.get('Note_personnelle', '')
                note_html = f"<p><strong>Note :</strong> {note}</p>" if note else ""
                
                # Ajout des nouvelles informations avec gestion des valeurs nulles
                description = j.get('Description', '')
                description_html = f"<p><strong>Description :</strong> {description}</p>" if description else ""
                
                temps = j.get('Temps_moyen_termine', 0)
                categorie_temps = get_categorie_temps(temps)
                temps_html = f"""<p><strong>Durée : </strong><span style="{get_style_temps(temps)}">{temps}h ({categorie_temps})</span></p>""" if temps else ""
                
                genre = j.get('Genre', '')
                genre_html = f"""<p><strong>Genre : </strong><span style="{get_style_genre(genre)}">{genre}</span></p>""" if genre else ""
                
                editeur = j.get('Editeur', '')
                editeur_html = f"<p><strong>Éditeur :</strong> {editeur}</p>" if editeur else ""
                
                plateforme = j.get('Plateforme', '')
                plateforme_html = f"<p><strong>Plateforme :</strong> {plateforme}</p>" if plateforme else ""
                
                etat_actuel = j.get('Etat', 'Non commencé')
                prochain_etat = get_prochain_etat(etat_actuel)
                
                jeux_html += f"""
                <div class="game-card">
                    <h3>{j.get('Titre', 'Jeu sans titre')}</h3>
                    <p><strong>État : </strong><span style="{get_style_etat(etat_actuel)}">{etat_actuel}</span></p>
                    <p><strong>Ajouté le :</strong> {j['Ajoute_le'].strftime('%d/%m/%Y')}</p>
                    {description_html}
                    {temps_html}
                    {genre_html}
                    {editeur_html}
                    {plateforme_html}
                    {note_html}
                    <div class="card-actions">
                        <button onclick="changerEtat('{j['ID']}')" class="btn-etat" 
                                style="background: {get_couleur_etat(etat_actuel)}"
                                title="Cliquer pour passer à : {etat_actuel} → {prochain_etat}">
                            Changer l'état ({etat_actuel})
                        </button>
                        <button onclick="openPopupPartage('{j['ID']}')" class="btn-partage">Partager</button>
                        <button onclick="supprimerJeu('{j['ID']}')" class="btn-suppr">Supprimer</button>
                    </div>
                </div>
                """
        else:
            jeux_html = "<p class='empty-list'>Ta liste est vide. Ajoute des jeux depuis la liste publique !</p>"

        # Liens conditionnels selon connexion/admin
        admin_link = f"<a href='/admin'>Admin</a>" if user and user.get('is_admin') else ""
        ma_liste_link = "<a href='/mes-jeux'>Ma liste</a>" if user else ""

        # Auth actions à droite
        login_actions = (
            f"<span class='user-info'>{user['Nom']}</span> "
            "<a href='/logout' class='btn'>Déconnexion</a>"
        )

        # Injection dans le HTML
        html = open("templates/ma_liste.html", encoding='utf-8').read()
        html = html.replace("{{title}}", "Ma Liste - Le_Backlog")
        html = html.replace("{{liste_jeux}}", jeux_html)
        html = html.replace("{{login_actions}}", login_actions)
        html = html.replace("{{admin_link}}", admin_link)
        html = html.replace("{{ma_liste_link}}", ma_liste_link)

        return html

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def changer_etat_jeu_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        data = cherrypy.request.json
        jeu_id = data.get("jeu_id")
        res = changer_etat_jeu(user_id, jeu_id)
        if res is True:
            return {"success": True}
        else:
            return {"success": False, "error": str(res)}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def supprimer_jeu_perso_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        data = cherrypy.request.json
        jeu_id = data.get("jeu_id")
        res = supprimer_jeu_perso(user_id, jeu_id)
        if res is True:
            return {"success": True}
        else:
            return {"success": False, "error": str(res)}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def partager_jeu_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        
        data = cherrypy.request.json
        success, message = partager_jeu(
            user_id=user_id,
            cible_pseudo=data.get('cible_pseudo'),
            listeperso_id=data.get('jeu_id'),
            message=data.get('message', '')
        )
        
        return {"success": success, "error": message if not success else None}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def tirer_au_sort_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        
        # On est sur la page ma_liste, donc on utilise tirage_jeu_ma_liste
        jeu = tirage_jeu_ma_liste(user_id)
        if jeu:
            return {"success": True, "jeu": jeu}
        return {"success": False, "error": "Aucun jeu disponible"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def tirer_au_sort_public_ajax(self):
        # Pour la page d'accueil, on utilise tirage_jeu_publique
        jeu = tirage_jeu_publique()
        if jeu:
            return {"success": True, "jeu": jeu}
        return {"success": False, "error": "Aucun jeu disponible"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def ajouter_jeu_publique(self, jeu_id):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        
        try:
            res = ajouter_jeu_perso_public(user_id, jeu_id)
            if res is True:
                return {"success": True, "message": "Jeu ajouté à votre liste"}
            else:
                return {"success": False, "error": str(res)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def stats_liste_ajax(self):
        try:
            user_id = cherrypy.session.get("user_id")
            if not user_id:
                return {"success": False, "error": "Non connecté"}
            
            stats = stats_liste_perso(user_id)
            
            # Préparation des données pour le graphique en camembert
            etats = {
                "Non commencé": stats["etats"].get("Non commencé", 0),
                "En cours": stats["etats"].get("En cours", 0),
                "Terminé": stats["etats"].get("Terminé", 0),
                "Abandonné": stats["etats"].get("Abandonné", 0)
            }
            
            # Vérifier s'il y a des données
            total = sum(etats.values())
            if total == 0:
                return {
                    "success": True,
                    "stats": {
                        "total": 0,
                        "etats": etats,
                        "genres_data": [],
                        "genre_favori": "Aucun"
                    },
                    "chart": None
                }
            
            try:
                # Création du graphique en camembert avec Matplotlib
                plt.figure(figsize=(16, 18))  # Plus haut pour accommoder la légende en liste
                plt.rcParams.update({'font.size': 28})  # Augmentation de la taille de police par défaut
                colors = ['#6c757d', '#007bff', '#28a745', '#dc3545']
                
                # Données pour le graphique
                labels = list(etats.keys())
                sizes = list(etats.values())
                
                # Créer le graphique en camembert sans labels
                patches, _ = plt.pie(sizes, colors=colors, startangle=90, labels=None)
                plt.axis('equal')
                plt.title('État des jeux', pad=20, color='white', fontsize=35, fontweight='bold')
                
                # Créer la légende personnalisée en dessous avec une police plus grande
                legend_labels = [f'{label} : {size} ({(size/total)*100:.1f}%)' for label, size in zip(labels, sizes)]
                legend = plt.legend(patches, legend_labels, 
                          loc='center',
                          bbox_to_anchor=(0.5, -0.25),  # Ajusté pour la nouvelle taille
                          ncol=1,  # Une seule colonne pour format liste
                          labelcolor='white',
                          facecolor='none',
                          edgecolor='none',
                          fontsize=32,  # Taille de police augmentée
                          title='Répartition des jeux',
                          title_fontsize=33,
                          frameon=False,  # Pas de cadre autour de la légende
                          labelspacing=1.2)  # Plus d'espace entre les éléments
                
                # Mettre le titre de la légende en blanc
                legend.get_title().set_color('white')
                
                # Ajuster les marges pour la légende en dessous
                plt.subplots_adjust(bottom=0.3)
                
                # Configurer le style pour le thème sombre
                plt.gca().set_facecolor('none')
                plt.gcf().patch.set_facecolor('none')
                
                # Convertir le graphique en image base64 avec une meilleure résolution
                buffer = BytesIO()
                plt.savefig(buffer, format='png', transparent=True, bbox_inches='tight', dpi=150)
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                plt.close()
                
                # Encoder en base64
                chart_data = base64.b64encode(image_png).decode('utf-8')
                
                return {
                    "success": True,
                    "stats": {
                        "total": total,
                        "etats": etats,
                        "genres_data": stats["genres_data"],
                        "genre_favori": stats["genre_favori"]
                    },
                    "chart": chart_data
                }
            except Exception as bokeh_error:
                return {
                    "success": True,
                    "stats": {
                        "total": total,
                        "etats": etats,
                        "genres_data": stats["genres_data"],
                        "genre_favori": stats["genre_favori"]
                    },
                    "chart": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "Erreur lors de la génération des statistiques"
            }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def jeux_partages_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        
        try:
            jeux = get_jeux_partages_reçus(user_id)
            for jeu in jeux:
                if 'Date_partage' in jeu:
                    jeu['Date_partage'] = jeu['Date_partage'].strftime('%d/%m/%Y %H:%M')
            return {"success": True, "jeux": jeux}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def supprimer_jeu_partage_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        
        data = cherrypy.request.json
        partage_id = data.get("partage_id")
        if not partage_id:
            return {"success": False, "error": "ID du partage manquant"}
        
        success, message = supprimer_jeu_partage_recu(user_id, partage_id)
        return {"success": success, "error": message if not success else None}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def ajouter_jeu_manuel_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        
        data = cherrypy.request.json
        titre = data.get('titre', '').strip()
        if not titre:
            return {"success": False, "error": "Le titre est obligatoire"}
        
        description = data.get('description', '').strip()
        genre = data.get('genre', '').strip()
        editeur = data.get('editeur', '').strip()
        plateforme = data.get('plateforme', '').strip()
        
        try:
            res = ajouter_jeu_perso_manuel(user_id, titre, description, genre, editeur, plateforme)
            if res is True:
                return {"success": True}
            else:
                return {"success": False, "error": str(res)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def ajouter_jeu_partage_ajax(self, liste_perso_id):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Vous devez être connecté"}
        
        try:
            # Récupérer les informations du jeu partagé
            jeu_info = get_jeu_partage_info(liste_perso_id)
            if not jeu_info:
                return {"success": False, "error": "Jeu partagé introuvable"}

            # Si c'est un jeu manuel (pas de Jeu_ID)
            if not jeu_info.get('Jeu_ID'):
                res = ajouter_jeu_perso_manuel(
                    user_id,
                    jeu_info['Titre'],
                    jeu_info.get('Description', ''),
                    jeu_info.get('Genre', ''),
                    jeu_info.get('Editeur', ''),
                    jeu_info.get('Plateforme', '')
                )
            else:
                # Si c'est un jeu de la liste publique
                res = ajouter_jeu_perso_public(user_id, jeu_info['Jeu_ID'])

            if res is True:
                return {"success": True, "message": "Jeu ajouté à votre liste"}
            else:
                return {"success": False, "error": str(res)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @cherrypy.expose
    def ma_liste(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            raise cherrypy.HTTPRedirect("/")
        
        user = get_user_by_id(user_id)
        
        # Liens conditionnels selon connexion/admin
        admin_link = f"<a href='/admin'>Admin</a>" if user and user.get('is_admin') else ""
        ma_liste_link = "<a href='/mes-jeux'>Ma liste</a>" if user else ""

        # Auth actions à droite
        login_actions = (
            f"<span class='user-info'>{user['Nom']}</span> "
            "<a href='/logout' class='btn'>Déconnexion</a>"
        )

        # Injection dans le HTML
        html = open("templates/ma_liste.html", encoding='utf-8').read()
        html = html.replace("{{title}}", "Ma Liste - Le_Backlog")
        html = html.replace("{{login_actions}}", login_actions)
        html = html.replace("{{admin_link}}", admin_link)
        html = html.replace("{{ma_liste_link}}", ma_liste_link)
        
        return html

    @cherrypy.expose
    def admin(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            raise cherrypy.HTTPRedirect("/")
        
        user = get_user_by_id(user_id)
        if not user or not user.get('is_admin'):
            raise cherrypy.HTTPRedirect("/")
        
        # Liens conditionnels selon connexion/admin
        admin_link = f"<a href='/admin'>Admin</a>" if user and user.get('is_admin') else ""
        ma_liste_link = "<a href='/mes-jeux'>Ma liste</a>" if user else ""

        # Auth actions à droite
        login_actions = (
            f"<span class='user-info'>{user['Nom']}</span> "
            "<a href='/logout' class='btn'>Déconnexion</a>"
        )

        # Injection dans le HTML
        html = open("templates/admin.html", encoding='utf-8').read()
        html = html.replace("{{login_actions}}", login_actions)
        html = html.replace("{{admin_link}}", admin_link)
        html = html.replace("{{ma_liste_link}}", ma_liste_link)
        
        return html

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_users_ajax(self):
        try:
            user_id = cherrypy.session.get("user_id")
            if not user_id:
                return {"success": False, "error": "Non connecté"}
            
            user = get_user_by_id(user_id)
            if not user or not user.get('is_admin'):
                return {"success": False, "error": "Accès non autorisé"}
            
            users = get_users()
            if not users and users != []:  # Si None ou autre valeur non valide
                return {"success": False, "error": "Erreur lors de la récupération des utilisateurs"}
            
            return {"success": True, "users": users}
        except Exception as e:
            print(f"Erreur dans get_users_ajax: {str(e)}")
            return {"success": False, "error": "Une erreur est survenue lors de la récupération des utilisateurs"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def delete_user_ajax(self):
        admin_id = cherrypy.session.get("user_id")
        if not admin_id:
            return {"success": False, "error": "Non connecté"}
        
        admin = get_user_by_id(admin_id)
        if not admin or not admin.get('is_admin'):
            return {"success": False, "error": "Accès non autorisé"}
        
        data = cherrypy.request.json
        success, message = delete_user(admin_id, data.get('user_id'))
        return {"success": success, "error": message if not success else None}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def promote_user_ajax(self):
        admin_id = cherrypy.session.get("user_id")
        if not admin_id:
            return {"success": False, "error": "Non connecté"}
        
        admin = get_user_by_id(admin_id)
        if not admin or not admin.get('is_admin'):
            return {"success": False, "error": "Accès non autorisé"}
        
        data = cherrypy.request.json
        success, message = set_user_admin(data.get('user_id'))
        return {"success": success, "error": message if not success else None}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_games_ajax(self):
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Non connecté"}
        
        user = get_user_by_id(user_id)
        if not user or not user.get('is_admin'):
            return {"success": False, "error": "Accès non autorisé"}
        
        games = get_all_jeux()
        return {"success": True, "games": games}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def delete_game_ajax(self):
        admin_id = cherrypy.session.get("user_id")
        if not admin_id:
            return {"success": False, "error": "Non connecté"}
        
        admin = get_user_by_id(admin_id)
        if not admin or not admin.get('is_admin'):
            return {"success": False, "error": "Accès non autorisé"}
        
        data = cherrypy.request.json
        success = supprimer_jeu(data.get('game_id'))
        return {"success": success is True, "error": str(success) if success is not True else None}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_suggestions_ajax(self):
        try:
            user_id = cherrypy.session.get("user_id")
            if not user_id:
                return {"success": False, "error": "Non connecté"}
            
            user = get_user_by_id(user_id)
            if not user or not user.get('is_admin'):
                return {"success": False, "error": "Accès non autorisé"}
            
            suggestions = get_all_suggestions()
            if suggestions is None:  # Si get_all_suggestions retourne None en cas d'erreur
                return {"success": False, "error": "Erreur lors de la récupération des suggestions"}
                
            # Convertir les objets datetime en chaînes pour la sérialisation JSON
            for suggestion in suggestions:
                if suggestion.get('Date_suggestion'):
                    suggestion['Date_suggestion'] = suggestion['Date_suggestion'].strftime('%Y-%m-%d %H:%M:%S')
            
            return {"success": True, "suggestions": suggestions}
            
        except Exception as e:
            cherrypy.log.error(f"Erreur dans get_suggestions_ajax: {str(e)}")
            return {"success": False, "error": f"Une erreur est survenue: {str(e)}"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def delete_suggestion_ajax(self):
        admin_id = cherrypy.session.get("user_id")
        if not admin_id:
            return {"success": False, "error": "Non connecté"}
        
        admin = get_user_by_id(admin_id)
        if not admin or not admin.get('is_admin'):
            return {"success": False, "error": "Accès non autorisé"}
        
        data = cherrypy.request.json
        success = delete_suggestion(data.get('suggestion_id'))
        return {"success": success is True, "error": "Erreur lors de la suppression" if not success else None}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def accept_suggestion_ajax(self):
        admin_id = cherrypy.session.get("user_id")
        if not admin_id:
            return {"success": False, "error": "Non connecté"}
        
        admin = get_user_by_id(admin_id)
        if not admin or not admin.get('is_admin'):
            return {"success": False, "error": "Accès non autorisé"}
        
        data = cherrypy.request.json
        suggestion_id = data.get('suggestion_id')
        
        # Récupérer les détails de la suggestion
        suggestion = get_suggestion(suggestion_id)
        if not suggestion:
            return {"success": False, "error": "Suggestion introuvable"}
        
        # Accepter la suggestion (ajouter le jeu et supprimer la suggestion)
        success = accepter_suggestion(
            suggestion_id,
            suggestion['Titre'],
            suggestion['Description'],
            suggestion['Temps_moyen_termine'],
            suggestion['Genre_ID'],
            suggestion['Editeur_ID'],
            suggestion['Plateforme_ID'],
            suggestion['Suggere_par']
        )
        
        return {"success": success is True, "error": "Erreur lors de l'acceptation" if not success else None}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def add_game_ajax(self):
        admin_id = cherrypy.session.get("user_id")
        if not admin_id:
            return {"success": False, "error": "Non connecté"}
        
        admin = get_user_by_id(admin_id)
        if not admin or not admin.get('is_admin'):
            return {"success": False, "error": "Accès non autorisé"}
        
        data = cherrypy.request.json
        titre = data.get('titre', '').strip()
        if not titre:
            return {"success": False, "error": "Le titre est obligatoire"}
        
        description = data.get('description', '').strip()
        temps = int(data.get('temps') or 0)
        genre_nom = data.get('genre', '').strip()
        editeur_nom = data.get('editeur', '').strip()
        plateforme_nom = data.get('plateforme', '').strip()
        
        # Récupérer ou créer les IDs pour genre, editeur et plateforme
        genre_id = get_or_create_id('Genres', genre_nom) if genre_nom else None
        editeur_id = get_or_create_id('Editeurs', editeur_nom) if editeur_nom else None
        plateforme_id = get_or_create_id('Plateformes', plateforme_nom) if plateforme_nom else None
        
        # Ajouter le jeu
        success = ajouter_jeu(titre, description, temps, genre_id, editeur_id, plateforme_id, admin_id)
        return {"success": success is True, "error": str(success) if success is not True else None}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def import_games_csv(self, *args, **kwargs):
        # Vérifier l'authentification
        user_id = cherrypy.session.get("user_id")
        if not user_id:
            raise cherrypy.HTTPError(401, "Non connecté")
        
        user = get_user_by_id(user_id)
        if not user or not user.get('is_admin'):
            raise cherrypy.HTTPError(403, "Accès non autorisé")
        
        if cherrypy.request.method == "POST":
            try:
                # Récupérer le contenu CSV depuis le JSON
                data = cherrypy.request.json
                content = data.get('content', '')
                
                # Vérifier que c'est bien un CSV
                if not content.strip():
                    return {"success": False, "error": "Fichier vide"}
                
                # Importer les jeux
                result = import_games_from_csv(content, user_id)
                
                if result["success"]:
                    message = f"{result['imported']} jeux importés avec succès."
                    if result["errors"]:
                        message += f" {len(result['errors'])} erreurs rencontrées."
                    return {"success": True, "message": message, "details": result}
                else:
                    return {"success": False, "error": result["error"]}
                
            except UnicodeDecodeError:
                return {"success": False, "error": "Le fichier doit être encodé en UTF-8"}
            except Exception as e:
                cherrypy.log.error(f"Erreur lors de l'import: {str(e)}")
                return {"success": False, "error": f"Erreur lors de l'import: {str(e)}"}
        else:
            raise cherrypy.HTTPError(405, "Méthode non autorisée")

if __name__ == "__main__":
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.sessions.timeout': 60,
            'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__))
        },
        '/api': {
            'tools.sessions.on': True,
            'tools.json_in.on': True,
            'tools.json_out.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')]
        }
    }
    
    # Configuration globale
    cherrypy.config.update({
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 8080,
        'server.max_request_body_size': 0,
        'tools.encode.on': True,
        'tools.encode.encoding': 'utf-8'
    })
    
    cherrypy.quickstart(MonApp(), '/', conf)
