# 🍳 Mes Recettes

Application interactive développée avec **Streamlit** pour répondre à un besoin spécifique **non couvert par les applications actuellement disponibles** sur les stores.

Les données (JSON) et les médias (Images/PDF) sont stockés directement sur le dépôt GitHub.

Ce projet a la particularité d'avoir été **entièrement développé à l'aide de l'IA Gemini** grâce à des **instructions précises et détaillées**.

## ✨ Fonctionnalités

* **🔒 Mode Consultation (Public)** : 
    * Recherche des recettes par nom, appareil (Cookeo, Thermomix, Ninja) ou ingrédient.
    * Partage de recttes par SMS.
    * Recette aléatoire dans un catégorie chosie.
    * Affichage du nombre de recette et du poid du dépot.
<br><br>
* **🔑 Mode administration (Connecté)** :  
   * **📚 Consultation des recettes** : 
       * Toutes les fonctions du mode public.
       * Modification et suppressions des recettes (sauf recette aléatoire et informations statistiques).
   * **✍️ Ajouter une recette** : Formulaire pour ajouter une recette.
   * **📚 Planing** : 
       * Organisation de la semaine (Midi & Soir).
       * Distinction visuelle : 📖 pour les recettes, ⚡ pour les plats rapides.
       * Visualisation des informations de la recette (catégorie, étapes, images...).
   * **🛠️ Maintenance** : 
       * Réparer l'index des recettes.
       * Sauvegarder le projet Github.
   * * **🚪 Déconnexion**

## 🛠️ Technologies utilisées

* **Python** : Langage principal du projet.
* **Streamlit** : Framework utilisé pour créer l'interface utilisateur web.
* **GitHub API** : Utilisée pour le stockage dynamique des données (fichiers JSON et images).
---

### 1. Prérequis
Vous devez disposer d'un compte GitHub et d'un jeton d'accès personnel (*** Fine-grained personal access tokens **) avec les permissions Read/Wrtie sur `Content `.

### 2. Configurer Streamlit Cloud
Dans votre interface Streamlit Cloud, allez dans **Settings** > **Secrets** et collez ceci en remplaçant par vos infos :

```toml
APP_PASSWORD = "votre_mot_de_passe"
GITHUB_TOKEN = "votre_token_ici"
REPO_OWNER = "votre_nom_utilisateur"
REPO_NAME = "nom_de_votre_depot"
```

### 3. Arborescence du projet
```
├── app.py                # Fichier principal
├── ajouterpy             # Module d'ajout
├── recettes.py           # Module de consultation et modification
├── planning.py           # Gestion du planning hebdomadaire
├── maintenance.py        # Outils de corrections et de contrôles
├── requirements.txt      # Liste des bibliothèques nécessaires
└── data/
    ├── recettes/                   # Dossier contenant les fichiers .json des recettes
    └── images/                     # Dossier contenant les photos et PDF
    ├── index_recettes.json         # Index pour recherche rapide
    ├── planning.json               # Données du planning
    ├── plats_rapides.json          # Liste des plats sans recette
```
