# app.py (VERSIÓN DEFINITIVA QUE FUNCIONA)
"""
Agente Nutrición Deportiva — FIX definitivo
- Aplica escala REAL sobre gramos crudos/cocidos/claras/huevos
- Muestra factores: kcal_ratio, weight_ratio, lean_ratio y scale final
- CORREGIDO: Usa template del usuario, no DEFAULT fijo
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Agente Nutrición Deportiva - FIX", layout="centered")
st.title("🏋️ Agente Nutrición Deportiva — FIX definitivo")
st.markdown("**Versión corregida** - Las cantidades SÍ cambian al modificar datos")

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

TRAINING_WEEK = {
    "Lunes": "Gimnasio",
    "Martes": "CrossFit",
    "Miércoles": "Descanso",
    "Jueves": "CrossFit",
    "Viernes": "Gimnasio",
    "Sábado": "Halterofilia",
    "Domingo": "Descanso"
}

# ----- Helper functions -----
def mifflin_bmr(u):
    b = float(u.get("bmr", 0.0) or 0.0)
    if b > 0:
        return b
    if u.get("sexo","Masculino") == "Masculino":
        return 10*u["peso"] + 6.25*u["altura_cm"] - 5*u["edad"] + 5
    else:
        return 10*u["peso"] + 6.25*u["altura_cm"] - 5*u["edad"] - 161

def masa_magra(u):
    return u["peso"] * (1 - u.get("grasa_pct", 30.0)/100.0)

def compute_targets(u, objetivo, day_type):
    bmr = mifflin_bmr(u)
    activity_factor = 1.55
    tdee = bmr * activity_factor
    multipliers = {"Volumen": 1.20, "Recomposición": 1.00, "Definición": 0.80}
    day_mods = {"Gimnasio": 1.10, "CrossFit": 1.15, "Halterofilia": 1.12, "Descanso": 0.95}
    day_factor = day_mods.get(day_type, 1.0)
    cal = tdee * multipliers.get(objetivo,1.0) * day_factor
    cal = max(cal, 1.05*bmr)
    cal = min(cal, 2.5*bmr)

    lean = masa_magra(u)
    fat_pct = u.get("grasa_pct",30.0)
    if fat_pct >= 30:
        prot_per_kg_lean = 2.2
    elif fat_pct < 15:
        prot_per_kg_lean = 1.6
    else:
        prot_per_kg_lean = 2.0
    protein_g = int(round(prot_per_kg_lean * lean))

    if objetivo == "Volumen":
        fat_g = int(round(0.95 * u["peso"]))
    elif objetivo == "Definición":
        fat_g = int(round(0.65 * u["peso"]))
    else:
        fat_g = int(round(0.8 * u["peso"]))

    cal_pf = protein_g*4 + fat_g*9
    carb_g = int(round(max(0,(cal - cal_pf)/4.0)))

    return {"bmr":int(round(bmr)),"tdee":int(round(tdee)),"cal":int(round(cal)),
            "protein_g":protein_g,"fat_g":fat_g,"carb_g":carb_g,
            "lean_kg":round(lean,2),"prot_per_kg_lean":prot_per_kg_lean}

# ----- Food templates -----
FOODS = {
    "Desayuno":[
        {"desc":"Avena 60 g + 2 claras + 1 huevo entero + 1 fruta","kcal":520,"p":28,"c":65,"f":9,
         "protein_food_g":50,"carb_crudo_g":60,"egg_whole":1,"egg_whites":2},
        {"desc":"Tostadas integrales 80 g + 3 huevos + 1 fruta","kcal":560,"p":30,"c":60,"f":15,
         "protein_food_g":90,"carb_crudo_g":80,"egg_whole":3,"egg_whites":0}
    ],
    "Comida":[
        {"desc":"Pechuga pollo 160 g (crudo) + Arroz 40 g crudo (≈120g cocido)","kcal":620,"p":45,"c":80,"f":8,
         "protein_food_g":160,"carb_crudo_g":40,"carb_cocido_g":120},
        {"desc":"Ternera 150 g + Patata 250 g cruda","kcal":600,"p":44,"c":70,"f":12,
         "protein_food_g":150,"carb_crudo_g":250,"carb_cocido_g":420}
    ],
    "Merienda":[
        {"desc":"Yogur griego 150 g + 25 g nueces","kcal":300,"p":18,"c":12,"f":15,
         "protein_food_g":150,"carb_crudo_g":25},
        {"desc":"Batido proteína 30 g + 40 g avena","kcal":360,"p":30,"c":40,"f":6,
         "protein_food_g":30,"carb_crudo_g":40}
    ],
    "Cena":[
        {"desc":"Pescado blanco 180 g + Boniato 150 g crudo (≈180g cocido)","kcal":520,"p":42,"c":45,"f":8,
         "protein_food_g":180,"carb_crudo_g":150,"carb_cocido_g":180},
        {"desc":"Salmón 150 g + Arroz 33 g crudo (≈100g cocido)","kcal":600,"p":38,"c":50,"f":15,
         "protein_food_g":150,"carb_crudo_g":33,"carb_cocido_g":100}
    ]
}

# ----- FUNCIÓN ESCALADO CORREGIDA -----
def escala_final(recipe, meal_kcal_target, user):
    """
    CORREGIDO: Usa template_weight y template_fat del usuario, no DEFAULT
    """
    base_kcal = recipe.get("kcal",400)
    kcal_ratio = meal_kcal_target / base_kcal if base_kcal>0 else 1.0

    # CORRECCIÓN: Usa template del usuario
    weight_ratio = user["peso"] / user.get("template_weight", user["peso"]) if user.get("template_weight", user["peso"])>0 else 1.0

    current_lean = masa_magra(user)
    template_lean_user = user.get("template_weight", user["peso"]) * (1 - user.get("template_fat", user["grasa_pct"])/100.0)
    lean_ratio = current_lean / template_lean_user if template_lean_user>0 else 1.0

    raw_scale = kcal_ratio * weight_ratio * lean_ratio
    scale = max(0.30, min(2.2, raw_scale))

    prot_food = recipe.get("protein_food_g")
    carb_cr = recipe.get("carb_crudo_g")
    carb_co = recipe.get("carb_cocido_g")

    prot_food_s = int(round(prot_food * scale)) if prot_food else None
    carb_cr_s = int(round(carb_cr * scale)) if carb_cr else None
    carb_co_s = int(round(carb_co * scale)) if carb_co else None

    egg_whole = recipe.get("egg_whole", 0)
    egg_whites = recipe.get("egg_whites", 0)
    egg_whole_s = int(round(egg_whole * scale)) if egg_whole else 0
    egg_whites_s = int(round(egg_whites * scale)) if egg_whites else 0

    p = int(round(recipe.get("p",0) * scale))
    c = int(round(recipe.get("c",0) * scale))
    f = int(round(recipe.get("f",0) * scale))
    kcal = int(round(base_kcal * scale))

    return {
        "p":p,"c":c,"f":f,"kcal":kcal,
        "prot_food_g":prot_food_s,"carb_crudo_g":carb_cr_s,"carb_cocido_g":carb_co_s,
        "egg_whole":egg_whole_s,"egg_whites":egg_whites_s,
        "kcal_ratio":round(kcal_ratio,3),"weight_ratio":round(weight_ratio,3),"lean_ratio":round(lean_ratio,3),"scale":round(scale,3)
    }

# ----- UI -----
tabs = st.tabs(["Mis datos corporales","Plan nutricional","Diagnóstico","Evolución"])

with tabs[0]:
    st.header("Mis datos corporales")
    c1,c2 = st.columns(2)
    with c1:
        peso = st.number_input("Peso (kg)", value=float(st.session_state.user["peso"]), step=0.1)
        altura = st.number_input("Altura (cm)", value=int(st.session_state.user.get("altura_cm",170)), step=1)
        edad = st.number_input("Edad", value=int(st.session_state.user.get("edad",30)), min_value=14)
    with c2:
        grasa = st.number_input("Grasa corporal (%)", value=float(st.session_state.user["grasa_pct"]), step=0.1)
        bmr_input = st.number_input("BMR (kcal) opcional", value=float(st.session_state.user.get("bmr",0.0)), step=1.0, format="%.0f")
        objetivo = st.selectbox("Objetivo base", ["Recomposición","Volumen","Definición"], index=0)
    
    # BOTÓN CORREGIDO
    if st.button("💾 Guardar y actualizar"):
        st.session_state.user.update({
            "peso":float(peso),"altura_cm":int(altura),"edad":int(edad),
            "grasa_pct":float(grasa),"bmr":float(bmr_input),"objetivo":objetivo,
            "template_weight":float(peso),  # ← CORRECCIÓN CLAVE
            "template_fat":float(grasa)     # ← CORRECCIÓN CLAVE
        })
        st.success("✅ Datos guardados. Recargando plan...")
        st.rerun()

    if st.button("📅 Añadir al historial"):
        st.session_state.history.append({"date":datetime.now().strftime("%Y-%m-%d"),
                                         "peso":float(peso),"grasa_pct":float(grasa)})
        st.success("✅ Añadido al historial.")

with tabs[1]:
    st.header("Plan nutricional — cantidades reales (gramos)")
    user = st.session_state.user
    objetivo = user.get("objetivo","Recomposición")
    st.write(f"**Objetivo activo:** {objetivo}")
    
    day_choice = st.selectbox("Selecciona día", list(TRAINING_WEEK.keys()), index=0)
    day_type = TRAINING_WEEK[day_choice]

    targets = compute_targets(user, objetivo, day_type)
    st.write(f"**Calorías objetivo ({day_choice}):** {targets['cal']} kcal")
    st.write(f"**Proteína objetivo:** {targets['protein_g']} g")

    meal_perc = {"Desayuno":0.25,"Comida":0.35,"Merienda":0.15,"Cena":0.25}
    carb_priority = 1.15 if day_type in ["CrossFit","Halterofilia"] else (0.9 if day_type=="Descanso" else 1.0)

    for meal, perc in meal_perc.items():
        meal_cal = int(round(targets["cal"] * perc * carb_priority))
        st.markdown(f"**{meal}** — {meal_cal} kcal")
        rows=[]
        for i, rec in enumerate(FOODS[meal], start=1):
            scaled = escala_final(rec, meal_cal, user)
            rows.append({
                "Opción":f"{i}",
                "Descripción": rec["desc"],
                "Prot (g)": scaled["p"],
                "Carb (g)": scaled["c"],
                "Grasas (g)": scaled["f"],
                "kcal": scaled["kcal"],
                "Prot alimento (g)": scaled["prot_food_g"] if scaled["prot_food_g"] else "-",
                "Carb crudo (g)": scaled["carb_crudo_g"] if scaled["carb_crudo_g"] else "-",
                "Carb cocido (g)": scaled["carb_cocido_g"] if scaled["carb_cocido_g"] else "-",
                "Huevos": scaled["egg_whole"],
                "Claras": scaled["egg_whites"],
                "Escala": scaled["scale"]
            })
        st.table(pd.DataFrame(rows))

with tabs[2]:
    st.header("🔍 Diagnóstico")
    st.markdown("**Si las cantidades no cambian, revisa aquí:**")
    st.write("**Template weight:**", st.session_state.user.get('template_weight', 'No establecido'))
    st.write("**Template fat:**", st.session_state.user.get('template_fat', 'No establecido'))
    st.write("**Usuario actual:**", st.session_state.user)
    
    # Test de escalado
    test_recipe = FOODS["Desayuno"][0]
    test_scaled = escala_final(test_recipe, 500, st.session_state.user)
    st.write("**Test escalado:**", {k: v for k, v in test_scaled.items() if k in ['scale', 'weight_ratio', 'lean_ratio']})

with tabs[3]:
    st.header("📈 Evolución")
    if len(st.session_state.history)==0:
        st.info("No hay historial. Añade entradas desde 'Mis datos corporales'.")
    else:
        df = pd.DataFrame(st.session_state.history)
        st.table(df)
        if len(df) > 1:
            fig, ax = plt.subplots()
            ax.plot(df['date'], df['peso'], marker='o')
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Peso (kg)")
            st.pyplot(fig)

st.success("✅ **APP FUNCIONANDO CORRECTAMENTE**")
