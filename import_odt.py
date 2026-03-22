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
    # On repère uniquement les lignes qui contiennent strictement "Ingrédients"
    indices_ing = [i for i, l in enumerate(lignes) if "Ingrédients" in l]
    
def extraire_donnees_odt(file_bytes):
    doc = opendocument.load(io.BytesIO(file_bytes))
    lignes = [teletype.extractText(p).strip() for p in doc.getElementsByType(text.P) if teletype.extractText(p).strip()]
    
    recettes = []
    # On trouve l'index de chaque ligne qui contient "Ingrédients"
    indices_ing = [i for i, l in enumerate(lignes) if "Ingrédients" in l]
    
    for i, start_idx in enumerate(indices_ing):
        # 1. LE TITRE : Uniquement la ligne juste avant "Ingrédients"
        # C'est le plus robuste pour éviter d'aspirer la recette précédente
        titre = lignes[start_idx - 1] if start_idx > 0 else "Nouvelle Recette"

        # 2. LA FIN DU BLOC : Jusqu'au prochain "Ingrédients" (moins 1 ligne pour le titre suivant)
        if i + 1 < len(indices_ing):
            end_idx = indices_ing[i+1] - 1
        else:
            end_idx = len(lignes)

        bloc_recette = lignes[start_idx:end_idx]
        texte_bloc = "\n".join(bloc_recette)
        
        # 3. SÉPARATION INGRÉDIENTS / PRÉPARATION
        # On cherche "Préparation" ou "Instructions" pour couper le bloc
        idx_prep = next((j for j, l in enumerate(bloc_recette) if re.search(r"Préparation|Instructions", l, re.I)), len(bloc_recette))
        
        lignes_ingredients = bloc_recette[1:idx_prep] 
        lignes_preparation = bloc_recette[idx_prep:]
        
        # 4. EXTRACTION DES TEMPS
        t_prep, t_cuisson = "", ""
        f_p = re.search(r"Préparation\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if f_p: t_prep = f_p.group(1)
        f_c = re.search(r"Cuisson\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if f_c: t_cuisson = f_c.group(1)

        # 5. PARSING DES INGRÉDIENTS
        ing_list = []
        for l in lignes_ingredients:
            match_nombre = re.match(r"^(\d+[g\s]*[a-zA-Z]*)\s+(.*)", l)
            if match_nombre:
                ing_list.append({"Ingrédient": match_nombre.group(2).strip(), "Quantité": match_nombre.group(1).strip()})
            else:
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
                _, cats_existantes = get_index_options()
                
                # Nettoyage : on s'assure que "---" n'est pas déjà dans cats_existantes
                autres_cats = sorted([c for c in cats_existantes if c and c != "---"])
                options_cat = ["---"] + autres_cats + ["➕ Ajouter une catégorie..."]
                
                # 1. Clé UNIQUE pour le selectbox (prefixe 'sb_')
                choix_cat = st.selectbox("Catégorie", options_cat, index=0, key=f"sb_{suffixe}")
                
                # Détermination de la catégorie finale
                if choix_cat == "➕ Ajouter une catégorie...":
                    # 2. Clé UNIQUE pour le texte (prefixe 'new_c_') 
                    # Cela évite le conflit avec le selectbox
                    cat_finale = st.text_input("Nom de la nouvelle catégorie", key=f"new_c_{suffixe}").strip()
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
                        for item in ing_df:
                            if "Ingrédient" in item and item["Ingrédient"]:
                                s = item["Ingrédient"].strip()
                                if len(s) > 0:
                                    # On prend la 1ère lettre en majuscule + le reste SANS le modifier
                                    item["Ingrédient"] = s[0].upper() + s[1:]
                                    
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
