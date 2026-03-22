import streamlit as st
import io, time, re
from odf import opendocument, text, teletype

from utils import (
    sauvegarder_recette_complete, 
    parser_ligne_ingredient, 
    get_index_options,
    verifier_doublon_recette,
    sauvegarder_recette_complete
)

def extraire_donnees_odt(file_bytes):
    doc = opendocument.load(io.BytesIO(file_bytes))
    lignes = [teletype.extractText(p).strip() for p in doc.getElementsByType(text.P) if teletype.extractText(p).strip()]
    
    recettes = []
    indices_ing = [i for i, l in enumerate(lignes) if "Ingrédients" in l]
    
    for i, start_idx in enumerate(indices_ing):
        titre = lignes[start_idx - 1] if start_idx > 0 else "Nouvelle Recette"

        if i + 1 < len(indices_ing):
            end_idx = indices_ing[i+1] - 1
        else:
            end_idx = len(lignes)

        bloc_recette = lignes[start_idx:end_idx]
        texte_bloc = "\n".join(bloc_recette)
        
        idx_prep = next((j for j, l in enumerate(bloc_recette) if re.search(r"Préparation|Instructions", l, re.I)), len(bloc_recette))
        
        lignes_ingredients = bloc_recette[1:idx_prep] 
        lignes_preparation = bloc_recette[idx_prep:]
        
        t_prep, t_cuisson = "", ""
        f_p = re.search(r"Préparation\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if f_p: t_prep = f_p.group(1)
        f_c = re.search(r"Cuisson\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if f_c: t_cuisson = f_c.group(1)

        ing_list = []
        for l in lignes_ingredients:
            parsed = parser_ligne_ingredient(l)
            if parsed:
                ing_list.append(parsed)
            else:
                ing_list.append({"Ingrédient": l, "Quantité": ""})
        
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
                liste_ing_existants, cats_existantes = get_index_options()
                autres_cats = sorted([c for c in cats_existantes if c and c != "---"])
                options_cat = ["---"] + autres_cats + ["➕ Ajouter une catégorie..."]
                
                choix_cat = st.selectbox("Catégorie", options_cat, index=0, key=f"sb_{suffixe}")
                
                if choix_cat == "➕ Ajouter une catégorie...":
                    cat_finale = st.text_input("Nom de la nouvelle catégorie", key=f"new_c_{suffixe}").strip()
                else:
                    cat_finale = choix_cat

            with col_app:
                appareils = ["Aucun", "Cookeo", "Thermomix", "Ninja", "Four"]
                appareil = st.selectbox("Appareil utilisé", options=appareils, key=f"a_{suffixe}")

            col_t1, col_t2 = st.columns(2)
            t_prep = col_t1.text_input("⏳ Temps Préparation", value=r['t_prep'], key=f"tp_{suffixe}", placeholder="Non détecté")
            t_cuis = col_t2.text_input("🔥 Temps Cuisson", value=r['t_cuisson'], key=f"tc_{suffixe}", placeholder="Non détecté")

            st.subheader("Ingrédients détectés")
            
            ing_uniques = {i for i in liste_ing_existants if i and i.strip() and i != "---"}
            options_suggestions = ["---"] + sorted(ing_uniques )

            liste_ordonnee = []
            for item in r['ing_list']:
                # On crée un nouveau dictionnaire avec l'ordre voulu
                nouvel_item = {
                    "Ingrédient": item.get("Ingrédient", ""),
                    "Suggestion": item.get("Suggestion", "---"),
                    "Quantité": item.get("Quantité", "")
                }
                liste_ordonnee.append(nouvel_item)
                
            ing_df = st.data_editor(liste_ordonnee, num_rows="dynamic",
                                    use_container_width=True,
                                    key=f"i_{suffixe}",
                                    column_config={
                                        "Ingrédient": st.column_config.TextColumn("Détecté", width="medium"),
                                        "Suggestion": st.column_config.SelectboxColumn(
                                            "Remplacer par...",
                                            options=options_suggestions,
                                            width="medium"
                                        ),
                                        "Quantité": st.column_config.TextColumn(width="small")
                                    })
                       
            st.subheader("Étapes de la recette")
            etapes = st.text_area("", value=r['prep_propre'], height=300, key=f"et_{suffixe}")

            st.divider()
            c_skip, c_save = st.columns(2)
            
            if c_skip.button("⏭️ Passer", use_container_width=True):
                st.session_state.import_idx += 1
                st.rerun()

            if c_save.button("✅ Enregistrer", type="primary", use_container_width=True):
                if not cat_finale or cat_finale == "---":
                    st.error("⚠️ Veuillez choisir une catégorie.")
                else:
                    with st.spinner("Sauvegarde..."):
                        # ON ENVOIE LE TABLEAU ing_df DIRECTEMENT
                        succes, nom_final = sauvegarder_recette_complete(
                            nom=nom, categorie=cat_finale, 
                            ingredients=ing_df, # On envoie les données brutes de l'éditeur
                            etapes=etapes, photos_files=None, 
                            appareil=appareil, t_prep=t_prep, t_cuis=t_cuis
                        )
                        if succes:
                            st.success(f"✅ '{nom_final}' enregistré !")
                            time.sleep(0.5)
                            st.session_state.liste_odt.pop(idx) # Enlève de la liste de traitement
                            if st.session_state.import_idx >= len(st.session_state.liste_odt):
                                st.session_state.import_idx = 0
                            st.rerun()
