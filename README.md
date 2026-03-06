# 🍳 Mes Recettes - (2026)

Application interactive développée avec **Streamlit** pour gérer vos recettes. Les données (JSON) et les médias (Images/PDF) sont stockés directement sur votre dépôt GitHub.

## ✨ Fonctionnalités

* **✍️ Saisie Manuelle** : Formulaire complet avec gestion des temps de préparation/cuisson et reset auto.
* **📥 Import Rapide** : Idéal pour scanner une recette papier via photo.
* **📚 Consultation Dynamique** : 
    * Recherche par nom, appareil (Cookeo, Thermomix, Ninja) ou ingrédient.
    * Galerie photo avec navigation fluide (Précédent/Suivant).
    * Mode modification pour corriger vos fiches à la volée.

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
- APP_PASSWORD = "votre_mot_de_passe"
GITHUB_TOKEN = "votre_token_ici"
REPO_OWNER = "votre_nom_utilisateur"
REPO_NAME = "nom_de_votre_depot"
```

### 3. Arborescence du projet
```
├── app.py                # Fichier principal (Gestion du menu)
├── saisir.py             # Module d'ajout manuel
├── importer.py           # Module d'import par photo
├── recettes.py           # Module de consultation et modification
├── requirements.txt      # Liste des bibliothèques nécessaires
└── data/
    ├── recettes/         # Dossier contenant les fichiers .json (vos recettes)
    └── images/           # Dossier contenant les photos et PDF
```
