# app.py - VERSIÓN CON DEBUG COMPLETO
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="DEBUG Nutrición", layout="centered")
st.title("🐛 DEBUG - Agente Nutrición")
st.markdown("**Versión con diagnóstico completo**")

# ----- Defaults -----
DEFAULT = {
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

if "user" not in st.session_state:
    st.session_state.user = DEFAULT.copy()
if "history" not in st.session_state:
    st.session_state.history = []

# ----- Funciones SIMPLIFICADAS pero FUNCIONALES -----
def masa_magra(u):
    return u["peso"] * (1 - u.get("grasa_pct", 30.0)/100.0)

def compute_targets(u):
    # Simplificado para debug
    base_cal = 2000
    if u["objetivo"] == "Volumen":
        cal = int(base_cal * 1.2)
    elif u["objetivo"] == "Definición":
        cal = int(base_cal * 0.8)
    else:
        cal = base_cal
    return {"cal": cal, "protein_g": int(u["peso"] * 2.0)}

# ----- Food templates -----
FOODS = {
    "Desayuno":[
        {"desc":"Avena 60g + 2 claras + 1 huevo","kcal":520,"p":28,"c":65,"f":9,
         "protein_food_g":50,"carb_crudo_g":60,"egg_whole":1,"egg_whites":2}
    ],
    "Comida":[
        {"desc":"Pollo 160g + Arroz 40g","kcal":620,"p":45,"c":80,"f":8,
         "protein_food_g":160,"carb_crudo_g":40}
    ]
}

# ----- FUNCIÓN ESCALADO CON DEBUG DETALLADO -----
def escala_final(recipe, meal_kcal_target, user):
    st.write("🔍 **DEBUG escala_final:**")
    st.write(f"   - User peso: {user['peso']}")
    st.write(f"   - User template_weight: {user.get('template_weight', 'NO EXISTE')}")
    st.write(f"   - User template_fat: {user.get('template_fat', 'NO EXISTE')}")
    
    base_kcal = recipe.get("kcal",400)
    kcal_ratio = meal_kcal_target / base_kcal
    
    # CALCULO DETALLADO DE weight_ratio
    user_template = user.get("template_weight", user["peso"])
    weight_ratio = user["peso"] / user_template
    st.write(f"   - weight_ratio: {user['peso']} / {user_template} = {weight_ratio}")
    
    # CALCULO DETALLADO DE lean_ratio  
    current_lean = masa_magra(user)
    template_lean = user_template * (1 - user.get("template_fat", user["grasa_pct"])/100.0)
    lean_ratio = current_lean / template_lean if template_lean > 0 else 1.0
    st.write(f"   - lean_ratio: {current_lean} / {template_lean} = {lean_ratio}")
    
    scale = kcal_ratio * weight_ratio * lean_ratio
    scale = max(0.5, min(2.0, scale))
    st.write(f"   - Escala final: {scale}")
    
    # Aplicar escala
    prot_food = int(round(recipe.get("protein_food_g", 0) * scale))
    carb_crudo = int(round(recipe.get("carb_crudo_g", 0) * scale))
    
    return {
        "prot_food_g": prot_food,
        "carb_crudo_g": carb_crudo, 
        "scale": round(scale, 3),
        "weight_ratio": round(weight_ratio, 3),
        "lean_ratio": round(lean_ratio, 3)
    }

# ----- UI PRINCIPAL -----
st.header("🎯 TEST DE ESCALADO")

# Mostrar estado actual
st.subheader("📊 Estado actual del usuario")
st.json(st.session_state.user)

# Controles para modificar datos
st.subheader("✏️ Modificar datos")

col1, col2 = st.columns(2)
with col1:
    nuevo_peso = st.number_input("Nuevo peso (kg)", value=float(st.session_state.user["peso"]), step=0.1, key="nuevo_peso")
    nueva_altura = st.number_input("Altura (cm)", value=int(st.session_state.user["altura_cm"]), step=1)
with col2:
    nueva_grasa = st.number_input("Grasa (%)", value=float(st.session_state.user["grasa_pct"]), step=0.1)
    nuevo_objetivo = st.selectbox("Objetivo", ["Recomposición","Volumen","Definición"], 
                                index=["Recomposición","Volumen","Definición"].index(st.session_state.user["objetivo"]))

# BOTÓN DE GUARDADO MEJORADO
if st.button("💾 GUARDAR DATOS (CON DEBUG)", type="primary"):
    st.write("🔄 **DEBUG Guardando datos...**")
    st.write(f"   - Peso anterior: {st.session_state.user['peso']}")
    st.write(f"   - Peso nuevo: {nuevo_peso}")
    st.write(f"   - Template_weight anterior: {st.session_state.user.get('template_weight', 'NO EXISTE')}")
    
    # GUARDAR CON template_weight CORRECTO
    st.session_state.user.update({
        "peso": float(nuevo_peso),
        "altura_cm": int(nueva_altura), 
        "grasa_pct": float(nueva_grasa),
        "objetivo": nuevo_objetivo,
        "template_weight": float(nuevo_peso),  # ¡IMPORTANTE!
        "template_fat": float(nueva_grasa)     # ¡IMPORTANTE!
    })
    
    st.write(f"   - Template_weight nuevo: {st.session_state.user['template_weight']}")
    st.success("✅ ¡Datos guardados CORRECTAMENTE!")
    st.rerun()

# TEST DE ESCALADO EN TIEMPO REAL
st.subheader("🧪 TEST EN TIEMPO REAL")

targets = compute_targets(st.session_state.user)
meal_cal = targets["cal"] * 0.3  # 30% para desayuno

st.write(f"**Calorías comida test:** {meal_cal} kcal")

for comida, recetas in FOODS.items():
    st.write(f"**{comida}**")
    for receta in recetas:
        st.write(f"Receta: {receta['desc']}")
        
        # Mostrar valores originales
        st.write(f"  - Original: {receta['protein_food_g']}g proteína, {receta['carb_crudo_g']}g carbos")
        
        # Aplicar escalado con DEBUG
        with st.expander("Ver cálculo detallado"):
            escalado = escala_final(receta, meal_cal, st.session_state.user)
        
        # Mostrar resultados
        st.write(f"  - Escalado: {escalado['prot_food_g']}g proteína, {escalado['carb_crudo_g']}g carbos")
        st.write(f"  - Factor escala: {escalado['scale']}")
        
        # VERIFICACIÓN CRÍTICA
        if escalado['weight_ratio'] == 1.0:
            st.error("❌ PROBLEMA: weight_ratio = 1.0 (NO hay cambio)")
        else:
            st.success(f"✅ OK: weight_ratio = {escalado['weight_ratio']} (SÍ hay cambio)")
        
        st.write("---")

# BOTÓN DE RESET
if st.button("🔄 Reset a valores por defecto"):
    st.session_state.user = DEFAULT.copy()
    st.success("✅ Reset completo")
    st.rerun()

st.markdown("---")
st.info("**INSTRUCCIONES DEBUG:** Cambia el peso → Haz clic en GUARDAR → Verifica que weight_ratio ≠ 1.0")
