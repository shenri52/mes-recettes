# 🍳 Mes Recettes - (2026)

Application interactive développée avec **Streamlit** pour gérer vos recettes. Les données (JSON) et les médias (Images/PDF) sont stockés directement sur votre dépôt GitHub.

## 🤖 Conception & IA
Ce projet a la particularité d'avoir été **entièrement développé à l'aide de l'IA Gemini** grâce à des **instructions précises et détaillées**. L'application a été structurée, codée et optimisée sans écriture manuelle de code.

## 🎯 But du projet
Répondre à un besoin spécifique **non couvert par les applications actuellement disponibles** sur les stores. L'objectif est d'offrir une solution sur mesure, légère et totalement maîtrisée pour la gestion quotidienne des repas.

## ✨ Fonctionnalités

* **🔒 Mode Consultation (Public)** : 
    * Recherche des recettes par nom, appareil (Cookeo, Thermomix, Ninja) ou ingrédient.  
* **🔑 Mode administration (Connecté)** :  
* **📚 Consultation des recettes** : 
    * Toutes les fonctions du mode public.
    * Modification et suppressions des recettes.
* **✍️ Saisie manuelle** : Formulaire complet avec gestion des temps de préparation/cuisson et reset auto.
* **📥 Import rapide** : Idéal pour scanner une recette papier via photo.

* **📚 Planing** : 
    * Organisation de la semaine (Midi & Soir).
    * Fusion des recettes enregistrées et des Plats Rapides (sans fiche).
    * Distinction visuelle : 📖 pour les recettes, ⚡ pour les plats improvisés.
    * Visualisation des informations de la recette (catégorie, étapes, images...)
* **📚 Gestion des courses** : 
    * Sasir la liste des courses (orgainsation actuelle selon mon parcours du magasin)
    * Module de visualisation optimisé pour faire ses courses sur mobile
* **🛠️ Maintenance** : 
    * Réparer l'index des recettes
    * Réparer le nom des ingrédients (ex : suppression des espaces superflus à la fin)
    * Optimiser les images sans perte de qualité
    * Modifier les ingrédients de la liste des courses et leur emplacement
* **🚫 Mode "Appli connecté" :
   * Option pour empêcher l'application de se déconnecter lors de la mise en veille du téléphone
* **📊 Statistiques :
   * Nombre de recette
   * Stockage


## 🛠️ Technologies utilisées

* **Python** : Langage principal du projet.
* **Streamlit** : Framework utilisé pour créer l'interface utilisateur web.
* **GitHub API** : Utilisée pour le stockage dynamique des données (fichiers JSON et images) sans nécessité de base de données externe.
* **PIL (Pillow)** : Bibliothèque dédiée au traitement, à l'optimisation et à la manipulation des images.
* 
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
├── saisir.py             # Module d'ajout manuel
├── importer.py           # Module d'import par photo
├── recettes.py           # Module de consultation et modification
├── planning.py           # Gestion du planning hebdomadaire
├── coursesaisir.py       # Préparation de la liste de courses
├── coursevisualiser.py   # Mode "Magasin" pour les courses
├── stats.py              # Statistiques d'utilisation
├── maintenance.py        # Outils de corrections et de contrôles
├── requirements.txt      # Liste des bibliothèques nécessaires
└── courses/
    
└── data/
    ├── recettes/                   # Dossier contenant les fichiers .json des recettes
    └── images/                     # Dossier contenant les photos et PDF
    ├── data_stockage.json          # Statistiques du dépôt
    ├── index_courses.json          # Index des produits utilisés pour les courses
    ├── index_produits_zones.json   # Index du classement des produits utilisés pour les courses
    ├── index_recettes.json         # Index pour recherche rapide
    ├── planning.json               # Données du planning
    ├── plats_rapides.json          # Liste des plats sans recette
```
