# 🍳 Mes Recettes - (2026)

Application interactive développée avec **Streamlit** pour gérer vos recettes. Les données (JSON) et les médias (Images/PDF) sont stockés directement sur votre dépôt GitHub.

## ✨ Fonctionnalités

* **✍️ Saisie Manuelle** : Formulaire complet avec gestion des temps de préparation/cuisson et reset auto.
* **📥 Import Rapide** : Idéal pour scanner une recette papier via photo.
* **📚 Consultation Dynamique** : 
    * Recherche par nom, appareil (Cookeo, Thermomix, Ninja) ou ingrédient.
    * Galerie photo avec navigation fluide (Précédent/Suivant).
    * Mode modification pour corriger vos fiches à la volée.

---

## ⚙️ Configuration GitHub (Indispensable)

Pour que l'application puisse écrire sur votre dépôt, vous devez configurer un jeton d'accès.

### 1. Créer le Token (PAT)
1. Allez dans vos **Settings** GitHub (Photo de profil > Settings).
2. Tout en bas à gauche : **Developer settings**.
3. **Personal access tokens** > **Tokens (classic)**.
4. Cliquez sur **Generate new token (classic)**.
5. Sélectionnez le scope : `repo` (accès complet aux dépôts).
6. Copiez le jeton généré (il ne s'affiche qu'une seule fois !).

### 2. Configurer Streamlit Cloud
Dans votre interface Streamlit Cloud, allez dans **Settings** > **Secrets** et collez ceci en remplaçant par vos infos :

```toml
GITHUB_TOKEN = "votre_token_ici"
REPO_OWNER = "votre_nom_utilisateur"
REPO_NAME = "nom_de_votre_depot"
```

### 3. Arborescence du projet
├── app.py                # Fichier principal (Gestion du menu)
├── saisir.py             # Module d'ajout manuel
├── importer.py           # Module d'import par photo
├── recettes.py           # Module de consultation et modification
├── requirements.txt      # Liste des bibliothèques nécessaires
└── data/
    ├── recettes/         # Dossier contenant les fichiers .json (vos recettes)
    └── images/           # Dossier contenant les photos et PDF
