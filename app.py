# app_v10.py
"""
Agente Nutrición Deportiva — V10 (Final)
- Escalado real de porciones por calorías objetivo
- Base ampliada de alimentos (varias alternativas)
- Mifflin-St Jeor, macros por masa magra
- 4 comidas/día
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Agente Nutrición V10", layout="centered")
st.title("🏋️‍♂️ Agente de Nutrición Deportiva — V10 (Final)")
st.markdown("Escalado real de porciones por calorías objetivo · Base ampliada de alimentos · 4 comidas")

# -------------------------
# Defaults (tu última medición)
# -------------------------
DEFAULT = {
    "peso": 92.1,
    "altura_cm": 186,
    "edad": 42,
    "sexo": "Masculino",
    "imc": 27.2,
    "grasa_pct": 37.9,
    "masa_muscular_kg": 53.2,
    "bmr": 1721.0,
    "objetivo": "Recomposición"
}

if "user" not in st.session_state:
    st.session_state.user = DEFAULT.copy()
if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------
# Helper functions
# -------------------------
def mifflin_bmr(u):
    b = float(u.get("bmr", 0.0) or 0.0)
    if b > 0:
        return b
    if u.get("sexo", "Masculino") == "Masculino":
        return 10*u["peso"] + 6.25*u["altura_cm"] - 5*u["edad"] + 5
    else:
        return 10*u["peso"] + 6.25*u["altura_cm"] - 5*u["edad"] - 161

def lean_mass(u):
    return u["peso"] * (1 - u.get("grasa_pct", 30.0)/100.0)

def compute_targets(u, objetivo, day_type):
    bmr = mifflin_bmr(u)
    activity_factor = 1.55
    tdee = bmr * activity_factor
    multipliers = {"Volumen":1.15, "Recomposición":1.00, "Definición":0.80}
    day_mods = {"Gimnasio":1.00, "Intenso":1.10, "Descanso":0.95}
    cal_target = tdee * multipliers.get(objetivo,1.0) * day_mods.get(day_type,1.0)
    # safety bounds
    cal_target = max(cal_target, 1.05*bmr)
    cal_target = min(cal_target, 2.5*bmr)

    # protein per kg lean
    lean = lean_mass(u)
    fat_pct = u.get("grasa_pct",30.0)
    if fat_pct >= 30:
        prot_g_per_kg_lean = 2.2
    elif fat_pct < 15:
        prot_g_per_kg_lean = 1.6
    else:
        prot_g_per_kg_lean = 2.0
    protein_g = int(round(prot_g_per_kg_lean * lean))

    # fats g/kg bodyweight by objective
    if objetivo == "Volumen":
        fat_g = int(round(0.95 * u["peso"]))
    elif objetivo == "Definición":
        fat_g = int(round(0.65 * u["peso"]))
    else:
        fat_g = int(round(0.8 * u["peso"]))

    cal_pf = protein_g*4 + fat_g*9
    carb_g = int(round(max(0, (cal_target - cal_pf)/4.0)))

    return {"bmr":int(round(bmr)), "tdee":int(round(tdee)), "cal":int(round(cal_target)),
            "protein_g":protein_g, "fat_g":fat_g, "carb_g":carb_g,
            "lean_kg":round(lean,1), "prot_per_kg_lean":prot_g_per_kg_lean}

# -------------------------
# Food database (expanded) — each item: desc, kcal_template, p,c,f, protein_food_g, carb_crudo_g, carb_cocido_g
# Values are templates (typical portions)
# -------------------------
FOODS = {
    "Desayuno":[
        {"desc":"Avena 60 g + 2 claras + 1 huevo + 1 fruta","kcal":520,"p":28,"c":65,"f":9,"protein_food_g":50,"carb_crudo_g":60},
        {"desc":"Tostadas integrales 80 g + 3 huevos + 1 fruta","kcal":560,"p":30,"c":60,"f":15,"protein_food_g":90,"carb_crudo_g":80},
        {"desc":"Yogur griego 200 g + granola 50 g + fruta","kcal":450,"p":22,"c":55,"f":12,"protein_food_g":200,"carb_crudo_g":50},
        {"desc":"Tortilla avena (40g avena) + claras + fruta","kcal":480,"p":32,"c":52,"f":8,"protein_food_g":80,"carb_crudo_g":40}
    ],
    "Comida":[
        {"desc":"Pechuga pollo 160 g + Arroz 120 g cocido + Verduras","kcal":620,"p":45,"c":80,"f":8,"protein_food_g":160,"carb_crudo_g":40,"carb_cocido_g":120},
        {"desc":"Ternera magra 150 g + Patata 250 g cruda + Ensalada","kcal":600,"p":44,"c":70,"f":12,"protein_food_g":150,"carb_crudo_g":250,"carb_cocido_g":420},
        {"desc":"Lomo cerdo 160 g + Pasta 90 g cruda + Verduras","kcal":650,"p":46,"c":85,"f":10,"protein_food_g":160,"carb_crudo_g":90},
        {"desc":"Salmón 150 g + Quinoa 80 g cocida + Verduras","kcal":700,"p":40,"c":75,"f":20,"protein_food_g":150,"carb_crudo_g":50,"carb_cocido_g":120}
    ],
    "Merienda":[
        {"desc":"Yogur griego 150 g + 25 g nueces","kcal":300,"p":18,"c":12,"f":15,"protein_food_g":150,"carb_crudo_g":25},
        {"desc":"Batido proteína 30 g + 40 g avena","kcal":360,"p":30,"c":40,"f":6,"protein_food_g":30,"carb_crudo_g":40},
        {"desc":"Requesón 150 g + 1 fruta + 20 g semillas","kcal":260,"p":20,"c":18,"f":8,"protein_food_g":150}
    ],
    "Cena":[
        {"desc":"Pescado blanco 180 g + Boniato 150 g crudo + Verduras","kcal":520,"p":42,"c":45,"f":8,"protein_food_g":180,"carb_crudo_g":150,"carb_cocido_g":180},
        {"desc":"Salmón 150 g + Arroz 100 g cocido + Verduras","kcal":600,"p":38,"c":50,"f":15,"protein_food_g":150,"carb_crudo_g":33,"carb_cocido_g":100},
        {"desc":"Tortilla 3 huevos + 100 g patata cocida + Ensalada","kcal":420,"p":28,"c":30,"f":18,"protein_food_g":180,"carb_crudo_g":100}
    ]
}

# -------------------------
# Scaling function: returns scaled macros and grams (crudo/cocido)
# -------------------------
def scale_recipe(recipe, meal_kcal_target, carb_priority_factor=1.0):
    """
    Scale recipe by kcal ratio. carb_priority_factor increases carbs relative to template
    (used in intense days).
    """
    base_kcal = recipe["kcal"]
    scale = meal_kcal_target / base_kcal if base_kcal>0 else 1.0
    # clamp scale
    scale = max(0.45, min(1.9, scale))

    # compute scaled macros proportionally
    p = int(round(recipe["p"] * scale))
    c = int(round(recipe["c"] * scale * carb_priority_factor))
    f = int(round(recipe["f"] * scale))
    kcal = int(round(recipe["kcal"] * scale * carb_priority_factor))

    # scale explicit grams
    prot_food = recipe.get("protein_food_g")
    carb_crudo = recipe.get("carb_crudo_g")
    carb_cocido = recipe.get("carb_cocido_g")
    prot_food_s = int(round(prot_food*scale)) if prot_food else None
    carb_crudo_s = int(round(carb_crudo*scale)) if carb_crudo else None
    carb_cocido_s = int(round(carb_cocido*scale)) if carb_cocido else None

    return {"p":p,"c":c,"f":f,"kcal":kcal,"scale":round(scale,2),
            "prot_food_g":prot_food_s,"carb_crudo_g":carb_crudo_s,"carb_cocido_g":carb_cocido_s}

# -------------------------
# UI: tabs
# -------------------------
tabs = st.tabs(["Mis datos corporales","Plan nutricional","Alternativas","Evolución"])

# Tab 0: Datos
with tabs[0]:
    st.header("Mis datos corporales")
    c1,c2 = st.columns(2)
    with c1:
        peso = st.number_input("Peso (kg)", value=float(st.session_state.user["peso"]), step=0.1)
        altura = st.number_input("Altura (cm)", value=int(st.session_state.user["altura_cm"]), step=1)
        edad = st.number_input("Edad", value=int(st.session_state.user["edad"]), min_value=14)
    with c2:
        grasa = st.number_input("Grasa corporal (%)", value=float(st.session_state.user["grasa_pct"]), step=0.1)
        masa_muscular = st.number_input("Masa muscular (kg)", value=float(st.session_state.user.get("masa_muscular_kg",0.0)), step=0.1)
        bmr_input = st.number_input("BMR (kcal) opcional", value=float(st.session_state.user.get("bmr",0.0)), step=1.0, format="%.0f")
    sexo = st.selectbox("Sexo", ["Masculino","Femenino"], index=0 if st.session_state.user.get("sexo","Masculino")=="Masculino" else 1)
    objetivo = st.selectbox("Objetivo", ["Recomposición","Volumen","Definición"], index=0)
    if st.button("Guardar y actualizar"):
        st.session_state.user.update({
            "peso":float(peso),"altura_cm":int(altura),"edad":int(edad),"grasa_pct":float(grasa),
            "masa_muscular_kg":float(masa_muscular),"bmr":float(bmr_input),"sexo":sexo,"objetivo":objetivo
        })
        st.success("Datos guardados.")
    if st.button("Añadir entrada a historial"):
        st.session_state.history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "peso": float(peso),
            "grasa_pct": float(grasa),
            "masa_muscular_kg": float(masa_muscular)
        })
        st.success("Entrada añadida al historial.")

# Tab 1: Plan nutricional
with tabs[1]:
    st.header("Plan nutricional — 4 comidas (escala real)")
    objetivo = st.session_state.user.get("objetivo","Recomposición")
    st.write("Objetivo activo:", objetivo)
    day_type = st.selectbox("Tipo de día (manual)", ["Gimnasio","Intenso","Descanso"], index=0)
    # compute targets
    targets = compute_targets(st.session_state.user, objetivo, day_type)
    st.subheader("Resumen energético")
    st.write(f"BMR: {targets['bmr']} kcal — TDEE (base): {targets['tdee']} kcal")
    st.write(f"Calorías objetivo: {targets['cal']} kcal")
    st.write(f"Proteínas: {targets['protein_g']} g — Grasas: {targets['fat_g']} g — Carbohidratos: {targets['carb_g']} g")
    st.write(f"Masa magra estimada: {targets['lean_kg']} kg — Prot/kg lean: {targets.get('prot_per_kg_lean')}")

    # pie chart macros
    macros_kcal = [targets["protein_g"]*4, targets["carb_g"]*4, targets["fat_g"]*9]
    fig, ax = plt.subplots(figsize=(3,3))
    ax.pie(macros_kcal, labels=["Proteínas","Carbohidratos","Grasas"], autopct="%1.0f%%", startangle=90)
    ax.axis("equal")
    st.pyplot(fig)

    # meal distribution (4 meals)
    meal_perc = {"Desayuno":0.25,"Comida":0.35,"Merienda":0.15,"Cena":0.25}
    carb_priority = 1.1 if day_type=="Intenso" else (0.95 if day_type=="Descanso" else 1.0)

    for meal, perc in meal_perc.items():
        meal_cal = int(round(targets["cal"] * perc))
        meal_prot = int(round(targets["protein_g"] * perc))
        meal_carb = int(round(targets["carb_g"] * perc * carb_priority))
        meal_fat = int(round(targets["fat_g"] * perc))
        st.markdown(f"**{meal}** — objetivo ~{meal_cal} kcal • P {meal_prot}g • C {meal_carb}g • F {meal_fat}g")

        rows = []
        for i, recipe in enumerate(FOODS[meal], start=1):
            scaled = scale_recipe(recipe, meal_cal, carb_priority_factor=carb_priority)
            prot_gap = meal_prot - scaled["p"]
            suggestion = ""
            if prot_gap > 0:
                # approx powder: 80% protein -> 1g protein ≈1.25g powder
                powder_g = int(round(prot_gap*1.25))
                suggestion = f"Añadir ~{prot_gap} g proteína (≈{powder_g} g polvo)"
            rows.append({
                "Opción":f"Opción {i}",
                "Descripción":recipe["desc"],
                "Proteínas (g)":scaled["p"],
                "Carbohidratos (g)":scaled["c"],
                "Grasas (g)":scaled["f"],
                "kcal aprox":scaled["kcal"],
                "Prot alimento g (crudo)": scaled["prot_food_g"] if scaled["prot_food_g"] else "-",
                "Carb crudo (g)": scaled["carb_crudo_g"] if scaled["carb_crudo_g"] else "-",
                "Carb cocido (g)": scaled["carb_cocido_g"] if scaled["carb_cocido_g"] else "-",
                "Sugerencia": suggestion
            })
        st.table(pd.DataFrame(rows))

# Tab 2: Alternativas
with tabs[2]:
    st.header("Catálogo de alternativas")
    catalog = []
    for meal, recs in FOODS.items():
        for r in recs:
            catalog.append({"Comida":meal,"Opción":r["desc"],"kcal":r["kcal"],"p(g)":r["p"],"c(g)":r["c"],"f(g)":r["f"]})
    st.dataframe(pd.DataFrame(catalog))

# Tab 3: Evolución
with tabs[3]:
    st.header("Evolución")
    hist = st.session_state.history
    if len(hist)==0:
        st.info("No hay entradas. Añade desde 'Mis datos corporales'.")
    else:
        df = pd.DataFrame(hist)
        st.table(df)
        fig, ax = plt.subplots()
        ax.plot(df['date'], df['peso'], marker='o')
        ax.set_xlabel("Fecha"); ax.set_ylabel("Peso (kg)")
        st.pyplot(fig)
        fig2, ax2 = plt.subplots()
        ax2.plot(df['date'], df['grasa_pct'], marker='o', color='orange')
        ax2.set_xlabel("Fecha"); ax2.set_ylabel("Grasa corporal (%)")
        st.pyplot(fig2)

st.markdown("---")
st.caption("V10 — Escalado real de porciones. Si quieres, lo dejo como `app.py` y lo despliegas en Streamlit Cloud.")
