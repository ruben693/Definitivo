import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Nutrición Deportiva", layout="centered")
st.title("🏋️ Agente Nutrición Deportiva")

if "user" not in st.session_state:
    st.session_state.user = {
        "peso": 92.1, 
        "altura_cm": 186, 
        "edad": 42, 
        "sexo": "Masculino",
        "grasa_pct": 37.9, 
        "bmr": 1721.0, 
        "objetivo": "Recomposición",
        "template_weight": 92.1, 
        "template_fat": 37.9
    }

if "history" not in st.session_state:
    st.session_state.history = []

def masa_magra(u):
    return u["peso"] * (1 - u.get("grasa_pct", 30.0)/100.0)

def compute_targets(u):
    base_cal = 2000
    if u["objetivo"] == "Volumen":
        cal = int(base_cal * 1.2)
    elif u["objetivo"] == "Definición":
        cal = int(base_cal * 0.8)
    else:
        cal = base_cal
    
    lean = masa_magra(u)
    if u["grasa_pct"] >= 30:
        protein_g = int(lean * 2.2)
    elif u["grasa_pct"] < 15:
        protein_g = int(lean * 1.6)
    else:
        protein_g = int(lean * 2.0)
    
    return {"cal": cal, "protein_g": protein_g, "lean_kg": lean}

tab1, tab2, tab3 = st.tabs(["📊 Datos", "🍽️ Comida", "📈 Evolución"])

with tab1:
    st.header("Mis Datos Corporales")
    
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso (kg)", 
                              value=st.session_state.user["peso"], 
                              step=0.1)
        altura = st.number_input("Altura (cm)", 
                                value=st.session_state.user["altura_cm"], 
                                step=1)
    with col2:
        grasa = st.number_input("Grasa (%)", 
                               value=st.session_state.user["grasa_pct"], 
                               step=0.1)
        objetivo = st.selectbox("Objetivo", 
                               ["Recomposición", "Volumen", "Definición"],
                               index=0)
    
    if st.button("💾 Guardar Datos", type="primary"):
        st.session_state.user.update({
            "peso": peso, 
            "altura_cm": altura, 
            "grasa_pct": grasa, 
            "objetivo": objetivo
        })
        st.success("✅ Datos guardados!")
        st.rerun()
    
    if st.button("📅 Añadir al Historial"):
        st.session_state.history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "peso": peso, 
            "grasa_pct": grasa
        })
        st.success("✅ Añadido al historial!")

with tab2:
    st.header("Plan de Comidas")
    
    user = st.session_state.user
    targets = compute_targets(user)
    
    st.write(f"**Peso:** {user['peso']} kg")
    st.write(f"**Grasa:** {user['grasa_pct']}%")
    st.write(f"**Masa magra:** {targets['lean_kg']:.1f} kg")
    st.write(f"**Proteína objetivo:** {targets['protein_g']} g")
    st.write(f"**Calorías:** {targets['cal']} kcal")
    
    st.subheader("Comidas Ejemplo")
    
    ratio = user["peso"] / user["template_weight"]
    
    comidas = [
        {
            "nombre": "Desayuno", 
            "alimentos": [
                {"nombre": "Avena", "base": 60, "ajustado": int(60 * ratio)},
                {"nombre": "Claras", "base": 2, "ajustado": int(2 * ratio)},
                {"nombre": "Huevos", "base": 1, "ajustado": int(1 * ratio)}
            ]
        },
        {
            "nombre": "Comida", 
            "alimentos": [
                {"nombre": "Pollo", "base": 160, "ajustado": int(160 * ratio)},
                {"nombre": "Arroz", "base": 40, "ajustado": int(40 * ratio)}
            ]
        }
    ]
    
    for comida in comidas:
        st.write(f"**{comida['nombre']}**")
        for alimento in comida["alimentos"]:
            st.write(f"- {alimento['nombre']}: {alimento['base']}g → {alimento['ajustado']}g")

with tab3:
    st.header("Evolución")
    
    if not st.session_state.history:
        st.info("No hay datos en el historial.")
    else:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df)
        
        if len(df) > 1:
            fig, ax = plt.subplots()
            ax.plot(df['date'], df['peso'], marker='o')
            ax.set_xlabel('Fecha')
            ax.set_ylabel('Peso (kg)')
            st.pyplot(fig)

st.success("🎯 ¡App completamente funcional!")