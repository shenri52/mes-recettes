import streamlit as st
import io, time, re
from odf import opendocument, text, teletype

from utils import (
    sauvegarder_recette_complete, 
    parser_ligne_ingredient, 
    get_index_options,
    verifier_doublon_recette
)

def extraire_donnees_odt(file_bytes):
    doc = opendocument.load(io.BytesIO(file_bytes))
    lignes = [teletype.extractText(p).strip() for p in doc.getElementsByType(text.P) if teletype.extractText(p).strip()]
    
    recettes = []
    indices_ingredients = [i for i, l in enumerate(lignes) if "Ingrédients" in l]
    
    for i, start_idx in enumerate(indices_ingredients):
        # 1. TROUVER LE DÉBUT DU TITRE
        # Le titre commence juste après la fin de la recette précédente
        debut_titre = indices_ingredients[i-1] + 1 if i > 0 else 0
        
        # 2. EXTRAIRE LE TITRE (toutes les lignes entre la fin précédente et "Ingrédients")
        lignes_titre = lignes[debut_titre:start_idx]
        titre = " ".join(lignes_titre).strip() if lignes_titre else "Nouvelle Recette"

        # 3. TROUVER LA FIN DE LA RECETTE (Juste avant le début du titre SUIVANT)
        if i + 1 < len(indices_ingredients):
            # On cherche le titre de la recette d'après pour s'arrêter AVANT lui
            idx_next_ing = indices_ingredients[i+1]
            idx_prev_recette = indices_ingredients[i]
            # Le titre suivant commence après le dernier ingrédient/préparation
            # Pour faire simple : on s'arrête à la première ligne du titre suivant
            end_idx = idx_next_ing - 1
            # On remonte tant qu'on n'est pas sur le mot "Ingrédients" pour trouver le vrai début du bloc suivant
            # Mais pour éviter le mélange, on va simplement tronquer le bloc_recette plus bas.
        else:
            end_idx = len(lignes)

        bloc_recette = lignes[start_idx:end_idx]
        
        # --- NETTOYAGE DE SÉCURITÉ ---
        # Si le titre suivant a été aspiré (ce qui arrive avec end_idx), 
        # on coupe le bloc dès qu'on détecte une ligne qui appartient au titre suivant.
        # On sait que le titre suivant commence à debut_recherche de la boucle d'après.
        if i + 1 < len(indices_ingredients):
            # On calcule combien de lignes de titre il y a pour la recette d'après
            prochain_debut_titre = indices_ingredients[i] # Approximatif
            # Le plus simple : on s'arrête là où le titre suivant a été détecté
            nb_lignes_titre_suivant = len(lignes[indices_ingredients[i]+1:indices_ingredients[i+1]])
            # (Optionnel : affinement ici si besoin)

        texte_bloc = "\n".join(bloc_recette)
        
        # limitation zone Préparation
        idx_prep = next((j for j, l in enumerate(bloc_recette) if re.search(r"Préparation|Instructions", l, re.I)), len(bloc_recette))
        
        lignes_ingredients = bloc_recette[1:idx_prep] 
        lignes_preparation = bloc_recette[idx_prep:]
        
        # --- DETECTION TEMPS ---
        t_prep, t_cuisson = "", ""
        found_p = re.search(r"Préparation\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if found_p: t_prep = found_p.group(1)
        found_c = re.search(r"Cuisson\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if found_c: t_cuisson = found_c.group(1)

        # --- PARSING INGRÉDIENTS ---
        ing_list = []
        for l in lignes_ingredients:
            match_nombre = re.match(r"^(\d+[g\s]*[a-zA-Z]*)\s+(.*)", l)
            if match_nombre:
                ing_list.append({"Ingrédient": match_nombre.group(2).strip(), "Quantité": match_nombre.group(1).strip()})
            else:
                parsed = parser_ligne_ingredient(l)
                if parsed: ing_list.append(parsed)
                else: ing_list.append({"Ingrédient": l, "Quantité": ""})
        
        recettes.append({
            "nom": titre, 
            "ing_list": ing_list, 
            "prep_propre": "\n".join(lignes_preparation),
            "t_prep": t_prep, 
            "t_cuisson": t_cuisson
        })
    
    return recettes

def afficher():

    if 'import_idx' not in st.session_state: st.session_state.import_idx = 0
    if 'liste_odt' not in st.session_state: st.session_state.liste_odt = []

    file = st.file_uploader("Charger un document ODT", type="odt")

    if file and not st.session_state.liste_odt:
        with st.spinner("Analyse du document..."):
            st.session_state.liste_odt = extraire_donnees_odt(file.getvalue())
            st.rerun()

    if st.session_state.liste_odt:
        idx = st.session_state.import_idx
        if idx < len(st.session_state.liste_odt):
            r = st.session_state.liste_odt[idx]
            suffixe = f"{idx}_{len(st.session_state.liste_odt)}"
            
            st.write(f"### Vérification : {idx+1} / {len(st.session_state.liste_odt)}")
            st.progress((idx + 1) / len(st.session_state.liste_odt))
            
            nom = st.text_input("Titre de la recette", value=r['nom'], key=f"n_{suffixe}")
            if verifier_doublon_recette(nom):
                st.warning("⚠️ Ce nom existe déjà. À l'enregistrement, la date du jour sera ajoutée pour éviter d'écraser l'ancienne.")
            
            col_cat, col_app = st.columns(2)
            with col_cat:
                _, cats_existantes = get_index_options()
                # On force le choix avec "---" en premier
                options_cat = ["---"] + sorted([c for c in cats_existantes if c]) + ["➕ Ajouter une catégorie..."]
                
                choix_cat = st.selectbox("Catégorie", options_cat, index=0, key=f"c_{suffixe}")
                
                # Détermination de la catégorie finale
                if choix_cat == "➕ Ajouter une catégorie...":
                    cat_finale = st.text_input("Nom de la catégorie", key=f"c_{suffixe}").strip()
                else:
                    cat_finale = choix_cat

            with col_app:
                appareils = ["Aucun", "Cookeo", "Thermomix", "Ninja", "Four"]
                appareil = st.selectbox("Appareil utilisé", options=appareils, key=f"a_{suffixe}")

            # Champs temps (Vides si non détectés)
            col_t1, col_t2 = st.columns(2)
            t_prep = col_t1.text_input("⏳ Temps Préparation", value=r['t_prep'], key=f"tp_{suffixe}", placeholder="Non détecté")
            t_cuis = col_t2.text_input("🔥 Temps Cuisson", value=r['t_cuisson'], key=f"tc_{suffixe}", placeholder="Non détecté")

            st.subheader("Ingrédients détectés")
            ing_df = st.data_editor(r['ing_list'], num_rows="dynamic",
                                    use_container_width=True,
                                    key=f"i_{suffixe}",
                                    column_config={
                                        "Quantité": st.column_config.TextColumn(width="small"),
                                        "Ingrédient": st.column_config.TextColumn(width="large")
                                    })
                       
            # --- BLOC PRÉPARATION ---
            st.subheader("Étapes de la recette")

            # La zone de texte avec ton titre "Texte de la recette"
            etapes = st.text_area("", value=r['prep_propre'], height=300, key=f"et_{suffixe}")

            st.divider()
            c_skip, c_save = st.columns(2)
            
            if c_skip.button("⏭️ Passer", use_container_width=True):
                st.session_state.import_idx += 1
                st.rerun()

            if c_save.button("✅ Enregistrer", type="primary", use_container_width=True):
                # Sécurité Catégorie Obligatoire
                if not cat_finale or cat_finale == "---":
                    st.error("⚠️ Veuillez choisir ou ajouter une catégorie.")
                else:
                    with st.spinner("Sauvegarde..."):
                        # Correction API : Gestion des doublons avant l'envoi
                        nom_propre = nom.strip()
                        if verifier_doublon_recette(nom_propre):
                            # On ajoute la date pour que le nom de fichier soit unique sur GitHub
                            nom_propre = f"{nom_propre} ({time.strftime('%d-%m-%Y')})"
                        
                        # Appel sécurisé avec les noms exacts des arguments de la fonction 🛡️
                        succes = sauvegarder_recette_complete(
                            nom=nom_propre, 
                            categorie=cat_finale, 
                            ingredients=ing_df, 
                            etapes=etapes, 
                            image_file=None, 
                            appareil=appareil, 
                            t_prep=t_prep, 
                            t_cuisson=t_cuis
                        )
                        
                        if succes:
                            st.success(f"'{nom_propre}' enregistré !")
                            time.sleep(0.5)
                            st.session_state.liste_odt.pop(idx)
                            st.rerun()
        else:
            st.balloons()
            st.success("Toutes les recettes ont été traitées ! ✨")
            if st.button("Charger un nouveau fichier ODT"):
                st.session_state.liste_odt = []
                st.session_state.import_idx = 0
                st.rerun()
