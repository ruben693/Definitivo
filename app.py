# app_pro_v9.py
"""
Agente Nutrición Deportiva — V9 Pro
Versión profesional extendida:
- Cálculo Mifflin-St Jeor
- Proteína basada en masa magra
- Escalado real de porciones (crudo/cocido)
- Visualizaciones y checks de seguridad
- 4 comidas, varias alternativas por comida
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------------------
# Page config and small style
# ---------------------------
st.set_page_config(page_title="Agente Nutrición V9 Pro", layout="centered", initial_sidebar_state="collapsed")
st.title("🏋️‍♂️ Agente de Nutrición Deportiva — V9 Pro")
st.markdown("Versión profesional — recomposición por defecto. Interfaz pensada para móvil y presentación.")

# ---------------------------
# Default user baseline (from your scale)
# ---------------------------
DEFAULT_USER = {
    "peso": 92.1,            # kg
    "altura_cm": 186,
    "edad": 42,
    "sexo": "Masculino",
    "imc": 27.2,
    "grasa_pct": 37.9,
    "masa_grasa_kg": 34.9,
    "masa_muscular_kg": 53.2,
    "bmr": 1721.0,           # if your scale provides it
    "objetivo": "Recomposición"
}

# ---------------------------
# Session-state init
# ---------------------------
if "user" not in st.session_state:
    st.session_state.user = DEFAULT_USER.copy()
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------------------
# Helper / core functions
# ---------------------------
def mifflin_st_jeor(user):
    """Return BMR using Mifflin-St Jeor, unless user provided BMR>0."""
    bmr = float(user.get("bmr", 0.0) or 0.0)
    if bmr > 0:
        return bmr
    peso = user["peso"]
    altura = user["altura_cm"]
    edad = user["edad"]
    if user.get("sexo", "Masculino") == "Masculino":
        return 10*peso + 6.25*altura - 5*edad + 5
    else:
        return 10*peso + 6.25*altura - 5*edad - 161

def lean_mass_from(user):
    """Estimate lean mass from weight and fat% (simple): lean = weight * (1 - fat%)."""
    fat_pct = user.get("grasa_pct", 30.0)/100.0
    lean = user["peso"] * (1 - fat_pct)
    return lean

def compute_tdee_and_macros(user, objetivo="Recomposición", day_type="Gimnasio"):
    """
    Compute target calories and macros.
    - Uses activity_factor baseline 1.55 (tunable)
    - multipliers: Volumen +15%, Recomposición 0%, Definición -20%
    - Proteins: based on lean mass (g/kg lean) with safety caps
    """
    bmr = mifflin_st_jeor(user)
    activity_factor = 1.55  # chosen for your weekly schedule
    tdee_base = bmr * activity_factor

    multipliers = {"Volumen": 1.15, "Recomposición": 1.00, "Definición": 0.80}
    day_mods = {"Gimnasio": 1.00, "Intenso": 1.10, "Descanso": 0.95}
    cal_target = tdee_base * multipliers.get(objetivo, 1.0) * day_mods.get(day_type, 1.0)

    # safety: do not go below 1.05 * bmr or above 2.5 * bmr
    lower = 1.05 * bmr
    upper = 2.5 * bmr
    cal_target = max(cal_target, lower)
    cal_target = min(cal_target, upper)

    # protein based on lean mass (g/kg lean). Use 2.0-2.6 g/kg lean depending on fat%
    lean = lean_mass_from(user)
    fat_pct = user.get("grasa_pct", 30.0)
    if fat_pct >= 30:
        prot_per_kg_lean = 2.2
    elif fat_pct < 15:
        prot_per_kg_lean = 1.6
    else:
        prot_per_kg_lean = 2.0
    protein_g = int(round(prot_per_kg_lean * lean))

    # Fats: baseline 0.8 g/kg bodyweight adjusted by objective
    if objetivo == "Volumen":
        fat_g = int(round(0.95 * user["peso"]))
    elif objetivo == "Definición":
        fat_g = int(round(0.65 * user["peso"]))
    else:
        fat_g = int(round(0.8 * user["peso"]))

    # carbs = remaining calories
    cal_from_pf = protein_g * 4 + fat_g * 9
    carb_g = int(round(max(0, (cal_target - cal_from_pf) / 4.0)))

    return {
        "bmr": int(round(bmr)),
        "tdee_base": int(round(tdee_base)),
        "cal_target": int(round(cal_target)),
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carb_g": carb_g,
        "lean_kg": round(lean,1),
        "prot_per_kg_lean": prot_per_kg_lean
    }

def scale_recipe_to_meal(recipe, meal_kcal_target):
    """
    Scale a recipe (template) proportionally to the meal kcal target.
    recipe must contain keys: p,c,f,kcal and optionally protein_food_g, carb_crudo_g, carb_cocido_g
    Returns scaled numbers and suggested grams for main items.
    """
    base_kcal = recipe.get("kcal", 400)
    if base_kcal <= 0:
        scale = 1.0
    else:
        scale = meal_kcal_target / base_kcal

    # limit scale to reasonable range to avoid absurd portions
    scale = max(0.5, min(1.8, scale))

    scaled = {
        "p": int(round(recipe["p"] * scale)),
        "c": int(round(recipe["c"] * scale)),
        "f": int(round(recipe["f"] * scale)),
        "kcal": int(round(base_kcal * scale)),
        "scale": round(scale,2)
    }

    # scale explicit grams for protein food and carbs (if provided)
    if recipe.get("protein_food_g"):
        scaled["protein_food_g"] = int(round(recipe["protein_food_g"] * scale))
    else:
        scaled["protein_food_g"] = None
    if recipe.get("carb_crudo_g"):
        scaled["carb_crudo_g"] = int(round(recipe["carb_crudo_g"] * scale))
    else:
        scaled["carb_crudo_g"] = None
    if recipe.get("carb_cocido_g"):
        scaled["carb_cocido_g"] = int(round(recipe["carb_cocido_g"] * scale))
    else:
        scaled["carb_cocido_g"] = None

    return scaled

# ---------------------------
# Food database (templates)
# ---------------------------
# Each template has macros and typical grams. We will scale them per meal target.
FOODS = {
    "Desayuno":[
        {"desc":"Avena 60 g + 2 claras + 1 huevo + 1 fruta","p":28,"c":65,"f":9,"kcal":520,"protein_food_g":50,"carb_crudo_g":60},
        {"desc":"Tostadas integrales 80 g + 3 huevos + 1 fruta","p":30,"c":60,"f":15,"kcal":560,"protein_food_g":90,"carb_crudo_g":80},
        {"desc":"Yogur griego 200 g + granola 50 g + fruta","p":22,"c":55,"f":12,"kcal":450,"protein_food_g":200,"carb_crudo_g":50}
    ],
    "Comida":[
        {"desc":"Pechuga pollo 160 g + Arroz 120 g cocido + Verduras","p":45,"c":80,"f":8,"kcal":620,"protein_food_g":160,"carb_crudo_g":40,"carb_cocido_g":120},
        {"desc":"Ternera magra 150 g + Patata 250 g cruda + Verduras","p":44,"c":70,"f":12,"kcal":600,"protein_food_g":150,"carb_crudo_g":250,"carb_cocido_g":420},
        {"desc":"Lomo de cerdo 160 g + Pasta 90 g cruda + Verduras","p":46,"c":85,"f":10,"kcal":650,"protein_food_g":160,"carb_crudo_g":90}
    ],
    "Merienda":[
        {"desc":"Yogur griego 150 g + 25 g nueces","p":18,"c":12,"f":15,"kcal":300,"protein_food_g":150,"carb_crudo_g":25},
        {"desc":"Batido proteína 30 g + 40 g avena","p":30,"c":40,"f":6,"kcal":360,"protein_food_g":30,"carb_crudo_g":40},
        {"desc":"Requesón 150 g + 1 fruta + 20 g semillas","p":20,"c":18,"f":8,"kcal":260,"protein_food_g":150}
    ],
    "Cena":[
        {"desc":"Pescado blanco 180 g + Boniato 150 g crudo + Verduras","p":42,"c":45,"f":8,"kcal":520,"protein_food_g":180,"carb_crudo_g":150,"carb_cocido_g":180},
        {"desc":"Salmón 150 g + Arroz 100 g cocido + Verduras","p":38,"c":50,"f":15,"kcal":600,"protein_food_g":150,"carb_crudo_g":33,"carb_cocido_g":100},
        {"desc":"Tortilla 3 huevos + 100 g patata cocida + Ensalada","p":28,"c":30,"f":18,"kcal":420,"protein_food_g":180,"carb_crudo_g":100}
    ]
}

# ---------------------------
# Layout: Sidebar quick info
# ---------------------------
with st.sidebar:
    st.markdown("**Herramientas**")
    st.write("• Guarda datos en 'Mis datos corporales'.")
    st.write("• Selecciona objetivo y tipo de día en 'Plan nutricional'.")
    st.divider()
    st.markdown("Contacto / Nota:")
    st.caption("App preparada por un desarrollador senior en nutrición — lista para ajustar y escalar.")

# ---------------------------
# Tabs: UI
# ---------------------------
tabs = st.tabs(["Mis datos corporales","Plan nutricional","Alternativas","Evolución","Ajustes"])
# Tab 0: Datos
with tabs[0]:
    st.header("Mis datos corporales (base para cálculos)")
    c1, c2 = st.columns(2)
    with c1:
        peso = st.number_input("Peso (kg)", value=float(st.session_state.user["peso"]), step=0.1)
        imc = st.number_input("IMC", value=float(st.session_state.user.get("imc",0.0)), step=0.1)
        grasa_pct = st.number_input("Grasa corporal (%)", value=float(st.session_state.user.get("grasa_pct",0.0)), step=0.1)
    with c2:
        masa_muscular_kg = st.number_input("Masa muscular (kg)", value=float(st.session_state.user.get("masa_muscular_kg",0.0)), step=0.1)
        altura_cm = st.number_input("Altura (cm)", value=int(st.session_state.user.get("altura_cm",180)), step=1)
        edad = st.number_input("Edad (años)", value=int(st.session_state.user.get("edad",30)), min_value=14)
    sexo = st.selectbox("Sexo", ["Masculino","Femenino"], index=0 if st.session_state.user.get("sexo","Masculino")=="Masculino" else 1)
    b1, b2 = st.columns(2)
    with b1:
        bmr_input = st.number_input("BMR (kcal) (opcional)", value=float(st.session_state.user.get("bmr",0.0)), step=1.0, format="%.0f")
    with b2:
        objetivo_select = st.selectbox("Objetivo inicial", ["Recomposición","Volumen","Definición"], index=0)

    if st.button("Guardar y actualizar datos"):
        st.session_state.user.update({
            "peso": float(peso),
            "imc": float(imc),
            "grasa_pct": float(grasa_pct),
            "masa_muscular_kg": float(masa_muscular_kg),
            "altura_cm": int(altura_cm),
            "edad": int(edad),
            "sexo": sexo,
            "bmr": float(bmr_input),
            "objetivo": objetivo_select
        })
        st.success("Datos guardados. Ve a Plan nutricional para ver el ajuste.")
    if st.button("Añadir a historial y guardar"):
        st.session_state.history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "peso": float(peso),
            "grasa_pct": float(grasa_pct),
            "masa_muscular_kg": float(masa_muscular_kg)
        })
        st.success("Entrada añadida al historial.")

# Tab 1: Plan nutricional
with tabs[1]:
    st.header("Plan nutricional — dinámico y escalable")
    objetivo = st.session_state.user.get("objetivo","Recomposición")
    c1, c2, c3 = st.columns(3)
    if c1.button("🟩 Volumen"):
        objetivo = "Volumen"
    if c2.button("🟨 Recomposición"):
        objetivo = "Recomposición"
    if c3.button("🟥 Definición"):
        objetivo = "Definición"
    st.session_state.user["objetivo"] = objetivo
    st.markdown(f"**Objetivo activo:** {objetivo}")

    # day type manual selector
    day_type = st.selectbox("Tipo de día (manual)", ["Gimnasio","Intenso","Descanso"], index=0)
    results = compute_tdee_and_macros(st.session_state.user, objetivo, day_type)

    st.subheader("Resumen energético y macros (ajustado)")
    st.write(f"BMR usada: **{results['bmr']} kcal** — TDEE base: **{results['tdee_base']} kcal**")
    st.write(f"Calorías objetivo (día): **{results['cal_target']} kcal**")
    st.write(f"Proteínas: **{results['protein_g']} g** — Grasas: **{results['fat_g']} g** — Carbohidratos: **{results['carb_g']} g**")
    st.write(f"Masa magra estimada: **{results['lean_kg']} kg** • proteína objetivo: **{results['prot_per_kg_lean']} g/kg lean**")

    # macro pie chart
    try:
        macros = [results["protein_g"]*4, results["carb_g"]*4, results["fat_g"]*9]
        labels = ["Proteínas (kcal)","Carbohidratos (kcal)","Grasas (kcal)"]
        fig1, ax1 = plt.subplots(figsize=(3,3))
        ax1.pie(macros, labels=labels, autopct="%1.0f%%", startangle=90)
        ax1.axis("equal")
        st.pyplot(fig1)
    except Exception:
        st.write("No se pudo dibujar el gráfico de macros.")

    # meal distribution (4 meals)
    meal_perc = {"Desayuno":0.25, "Comida":0.35, "Merienda":0.15, "Cena":0.25}
    st.markdown("### Plan diario (4 comidas) — alternativas escaladas automáticamente")
    day_view = st.selectbox("Selecciona día visual (referencia)", ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"], index=0)

    # Show each meal scaled
    for meal, perc in meal_perc.items():
        meal_kcal_target = int(round(results["cal_target"] * perc))
        meal_prot_target = int(round(results["protein_g"] * perc))
        meal_carb_target = int(round(results["carb_g"] * perc))
        meal_fat_target = int(round(results["fat_g"] * perc))
        st.markdown(f"**{meal}** — objetivo ~{meal_kcal_target} kcal • P {meal_prot_target}g • C {meal_carb_target}g • F {meal_fat_target}g")

        rows = []
        for i, recipe in enumerate(FOODS[meal], start=1):
            scaled = scale_recipe_to_meal(recipe, meal_kcal_target)
            # compute protein gap (if scaled recipe protein < meal_prot_target) -> suggest supplement
            prot_gap = meal_prot_target - scaled["p"]
            suggestion = ""
            if prot_gap > 0:
                # suggest protein shake grams (assume 80% protein of powder -> 1g protein ≈1.25g powder)
                shake_g = int(round(prot_gap * 1.25))
                suggestion = f"Añadir ~{prot_gap} g proteína (ej. {shake_g} g polvo)"
            rows.append({
                "Opción": f"Opción {i}",
                "Descripción": recipe["desc"],
                "Proteínas (g)": scaled["p"],
                "Carbohidratos (g)": scaled["c"],
                "Grasas (g)": scaled["f"],
                "kcal aprox": scaled["kcal"],
                "Prot alimento (g, crudo)": scaled.get("protein_food_g", "-"),
                "Carb crudo (g)": scaled.get("carb_crudo_g", "-"),
                "Carb cocido (g)": scaled.get("carb_cocido_g", "-"),
                "Sugerencia proteína": suggestion
            })
        st.table(pd.DataFrame(rows))

# Tab 2: Alternativas (resumen)
with tabs[2]:
    st.header("Alternativas por comida (resumen rápido)")
    summary = []
    for meal, recipes in FOODS.items():
        for r in recipes:
            summary.append({"Comida": meal, "Opción": r["desc"], "p(g)": r["p"], "c(g)": r["c"], "f(g)": r["f"], "kcal": r["kcal"]})
    st.dataframe(pd.DataFrame(summary))

# Tab 3: Evolución
with tabs[3]:
    st.header("Evolución y seguimiento")
    if len(st.session_state.history) == 0:
        st.info("No hay entradas en el historial. Añade alguna desde 'Mis datos corporales'.")
    else:
        df_hist = pd.DataFrame(st.session_state.history)
        st.table(df_hist)
        fig, ax = plt.subplots()
        ax.plot(df_hist['date'], df_hist['peso'], marker='o')
        ax.set_xlabel("Fecha"); ax.set_ylabel("Peso (kg)"); ax.set_title("Evolución del peso")
        st.pyplot(fig)
        fig2, ax2 = plt.subplots()
        ax2.plot(df_hist['date'], df_hist['grasa_pct'], marker='o', color='orange')
        ax2.set_xlabel("Fecha"); ax2.set_ylabel("Grasa corporal (%)"); ax2.set_title("Evolución grasa corporal")
        st.pyplot(fig2)

# Tab 4: Ajustes (espacio para futuras funciones)
with tabs[4]:
    st.header("Ajustes y notas")
    st.markdown("- Esta versión V9 Pro calcula porciones y sugiere suplementos proteicos cuando el template no cubre la proteína objetivo.")
    st.markdown("- Para producción: conectar a base de datos, añadir login/usuarios, y un endpoint para sincronizar báscula.")
    if st.button("Forzar recalculo y refrescar"):
        st.experimental_rerun()

st.markdown("---")
st.caption("V9 Pro — Profesional. Si deseas, adapto plantillas, rangos o tipos de comidas antes de tu presentación.")
