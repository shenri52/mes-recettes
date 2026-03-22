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
    
    for i, start_idx in enumerate(indices_ing):
        # --- 1. LE TITRE (Sécurité maximale) ---
        # On regarde les 3 lignes avant "Ingrédients"
        # Mais on ne remonte pas plus haut que la fin de la recette précédente
        limite_haute = indices_ing[i-1] + 1 if i > 0 else 0
        search_start = max(limite_haute, start_idx - 3) 
        
        lignes_titre = lignes[search_start:start_idx]
        titre = " ".join(lignes_titre).strip() if lignes_titre else "Nouvelle Recette"

        # --- 2. LA FIN DE LA RECETTE ---
        # La recette s'arrête juste avant le début du titre suivant
        if i + 1 < len(indices_ing):
            # On s'arrête 3 lignes avant le prochain "Ingrédients" (là où commence son titre)
            end_idx = max(start_idx + 1, indices_ing[i+1] - 3)
        else:
            end_idx = len(lignes)

        bloc_recette = lignes[start_idx:end_idx]
        texte_bloc = "\n".join(bloc_recette)
        
        # --- 3. DÉCOUPAGE INGRÉDIENTS / PRÉPARATION ---
        idx_prep = next((j for j, l in enumerate(bloc_recette) if re.search(r"Préparation|Instructions", l, re.I)), len(bloc_recette))
        
        lignes_ingredients = bloc_recette[1:idx_prep] 
        lignes_preparation = bloc_recette[idx_prep:]
        
        # --- 4. TEMPS & PARSING ---
        t_prep, t_cuisson = "", ""
        f_p = re.search(r"Préparation\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if f_p: t_prep = f_p.group(1)
        f_c = re.search(r"Cuisson\s*[:\-]?\s*(\d+\s*(?:min|h|minutes))", texte_bloc, re.I)
        if f_c: t_cuisson = f_c.group(1)

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
