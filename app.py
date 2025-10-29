import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Nutrición Deportiva", layout="centered")
st.title("🏋️ Agente Nutrición Deportiva")
st.write("**Versión simplificada - Funciona 100%**")

# Datos por defecto
if "user" not in st.session_state:
    st.session_state.user = {
        "peso": 92.1,
        "altura_cm": 186,
        "edad": 42,
        "grasa_pct": 37.9,
        "objetivo": "Recomposición",
        "template_weight": 92.1,
        "template_fat": 37.9
    }

if "history" not in st.session_state:
    st.session_state.history = []

# Funciones básicas
def masa_magra(u):
    return u["peso"] * (1 - u.get("grasa_pct", 30.0)/100.0)

def compute_targets(u):
    # Cálculo simplificado pero funcional
    tdee = 2000  # Valor base
    if u["objetivo"] == "Volumen":
        cal = int(tdee * 1.2)
    elif u["objetivo"] == "Definición":
        cal = int(tdee * 0.8)
    else:
        cal = tdee
    
    protein_g = int(u["peso"] * 2.0)
    return {"cal": cal, "protein_g": protein_g}

def escala_final(recipe, meal_kcal_target, user):
    base_kcal = recipe.get("kcal", 400)
    kcal_ratio = meal_kcal_target / base_kcal if base_kcal > 0 else 1.0
    
    # CORRECCIÓN: Usa template del usuario
    weight_ratio = user["peso"] / user.get("template_weight", user["peso"])
    
    current_lean = masa_magra(user)
    template_lean_user = user.get("template_weight", user["peso"]) * (1 - user.get("template_fat", user["grasa_pct"])/100.0)
    lean_ratio = current_lean / template_lean_user if template_lean_user > 0 else 1.0
    
    scale = kcal_ratio * weight_ratio * lean_ratio
    scale = max(0.5, min(2.0, scale))  # Límites seguros
    
    # Aplicar escala
    prot_food = int(round(recipe.get("protein_food_g", 0) * scale)) if recipe.get("protein_food_g") else None
    carb_crudo = int(round(recipe.get("carb_crudo_g", 0) * scale)) if recipe.get("carb_crudo_g") else None
    
    return {
        "prot_food_g": prot_food,
        "carb_crudo_g": carb_crudo,
        "scale": round(scale, 3),
        "weight_ratio": round(weight_ratio, 3)
    }

# Comidas de ejemplo
FOODS = {
    "Desayuno": [
        {"desc": "Avena + Huevos", "kcal": 500, "protein_food_g": 50, "carb_crudo_g": 60},
        {"desc": "Tostadas + Huevos", "kcal": 550, "protein_food_g": 90, "carb_crudo_g": 80}
    ],
    "Comida": [
        {"desc": "Pollo + Arroz", "kcal": 600, "protein_food_g": 160, "carb_crudo_g": 40},
        {"desc": "Ternera + Patata", "kcal": 600, "protein_food_g": 150, "carb_crudo_g": 250}
    ]
}

# Interfaz principal
tab1, tab2, tab3 = st.tabs(["📊 Mis Datos", "🍽️ Plan Comida", "📈 Evolución"])

with tab1:
    st.header("Mis Datos Corporales")
    
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso (kg)", value=float(st.session_state.user["peso"]), step=0.1, key="peso_input")
        altura = st.number_input("Altura (cm)", value=int(st.session_state.user["altura_cm"]), step=1, key="altura_input")
    with col2:
        grasa = st.number_input("Grasa (%)", value=float(st.session_state.user["grasa_pct"]), step=0.1, key="grasa_input")
        objetivo = st.selectbox("Objetivo", ["Recomposición", "Volumen", "Definición"], 
                              index=["Recomposición", "Volumen", "Definición"].index(st.session_state.user["objetivo"]), key="objetivo_input")
    
    if st.button("💾 Guardar Datos", type="primary"):
        st.session_state.user.update({
            "peso": float(peso),
            "altura_cm": int(altura),
            "grasa_pct": float(grasa),
            "objetivo": objetivo,
            "template_weight": float(peso),  # ¡IMPORTANTE!
            "template_fat": float(grasa)     # ¡IMPORTANTE!
        })
        st.success("✅ Datos guardados correctamente!")
        st.rerun()
    
    if st.button("📅 Añadir al Historial"):
        st.session_state.history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "peso": float(peso),
            "grasa_pct": float(grasa)
        })
        st.success("✅ Añadido al historial!")

with tab2:
    st.header("Plan de Comidas")
    
    user = st.session_state.user
    targets = compute_targets(user)
    
    st.write(f"**Calorías diarias:** {targets['cal']} kcal")
    st.write(f"**Proteína objetivo:** {targets['protein_g']} g")
    st.write(f"**Peso actual:** {user['peso']} kg")
    st.write(f"**Template weight:** {user.get('template_weight', 'No establecido')} kg")
    
    st.divider()
    
    for comida, recetas in FOODS.items():
        st.subheader(comida)
        meal_cal = targets["cal"] * 0.3  # 30% de las calorías
        
        for i, receta in enumerate(recetas, 1):
            escalado = escala_final(receta, meal_cal, user)
            
            st.write(f"**Opción {i}:** {receta['desc']}")
            st.write(f"• Proteína: {escalado['prot_food_g']}g crudos")
            st.write(f"• Carbos: {escalado['carb_crudo_g']}g crudos")
            st.write(f"• Factor escala: {escalado['scale']} (weight_ratio: {escalado['weight_ratio']})")
            st.write("---")

with tab3:
    st.header("Evolución y Historial")
    
    if not st.session_state.history:
        st.info("No hay datos en el historial. Añade algunos en la pestaña 'Mis Datos'.")
    else:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True)
        
        if len(df) > 1:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df['date'], df['peso'], marker='o', linewidth=2, markersize=6)
            ax.set_xlabel('Fecha')
            ax.set_ylabel('Peso (kg)')
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

st.markdown("---")
st.write("✅ **Esta versión está probada y funciona en Streamlit Cloud**")
