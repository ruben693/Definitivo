# app.py (VERSIÓN CORREGIDA - % GRASO SÍ AFECTA)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Agente Nutrición", layout="centered")
st.title("🏋️ Agente Nutrición - % Graso FUNCIONA")
st.markdown("**CORREGIDO:** El % graso SÍ afecta proteína e hidratos")

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
    "Lunes": "Gimnasio", "Martes": "CrossFit", "Miércoles": "Descanso",
    "Jueves": "CrossFit", "Viernes": "Gimnasio", "Sábado": "Halterofilia", "Domingo": "Descanso"
}

# ----- Helper functions -----
def mifflin_bmr(u):
    b = float(u.get("bmr", 0.0) or 0.0)
    if b > 0: return b
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

    # ✅ CORRECCIÓN: % GRASO SÍ AFECTA LA PROTEÍNA
    lean = masa_magra(u)
    fat_pct = u.get("grasa_pct",30.0)
    
    # Cálculo DETALLADO de proteína según % graso
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

    return {
        "bmr": int(round(bmr)), "tdee": int(round(tdee)), "cal": int(round(cal)),
        "protein_g": protein_g, "fat_g": fat_g, "carb_g": carb_g,
        "lean_kg": round(lean,2), "prot_per_kg_lean": prot_per_kg_lean,
        "masa_magra": lean, "fat_pct": fat_pct  # ✅ DEBUG
    }

# ----- Food templates -----
FOODS = {
    "Desayuno":[
        {"desc":"Avena 60g + 2 claras + 1 huevo","kcal":520,"p":28,"c":65,"f":9,
         "protein_food_g":50,"carb_crudo_g":60,"egg_whole":1,"egg_whites":2},
        {"desc":"Tostadas 80g + 3 huevos","kcal":560,"p":30,"c":60,"f":15,
         "protein_food_g":90,"carb_crudo_g":80,"egg_whole":3,"egg_whites":0}
    ],
    "Comida":[
        {"desc":"Pollo 160g + Arroz 40g","kcal":620,"p":45,"c":80,"f":8,
         "protein_food_g":160,"carb_crudo_g":40,"carb_cocido_g":120},
        {"desc":"Ternera 150g + Patata 250g","kcal":600,"p":44,"c":70,"f":12,
         "protein_food_g":150,"carb_crudo_g":250,"carb_cocido_g":420}
    ]
}

def escala_final(recipe, meal_kcal_target, user):
    base_kcal = recipe.get("kcal",400)
    kcal_ratio = meal_kcal_target / base_kcal if base_kcal>0 else 1.0
    weight_ratio = user["peso"] / user.get("template_weight", user["peso"])
    
    current_lean = masa_magra(user)
    template_lean_user = user.get("template_weight", user["peso"]) * (1 - user.get("template_fat", user["grasa_pct"])/100.0)
    lean_ratio = current_lean / template_lean_user if template_lean_user>0 else 1.0

    scale = max(0.30, min(2.2, kcal_ratio * weight_ratio * lean_ratio))

    prot_food_s = int(round(recipe.get("protein_food_g", 0) * scale)) if recipe.get("protein_food_g") else None
    carb_cr_s = int(round(recipe.get("carb_crudo_g", 0) * scale)) if recipe.get("carb_crudo_g") else None
    
    p = int(round(recipe.get("p",0) * scale))
    c = int(round(recipe.get("c",0) * scale))
    f = int(round(recipe.get("f",0) * scale))
    kcal = int(round(base_kcal * scale))

    return {
        "p":p,"c":c,"f":f,"kcal":kcal,
        "prot_food_g":prot_food_s,"carb_crudo_g":carb_cr_s,
        "kcal_ratio":round(kcal_ratio,3),"weight_ratio":round(weight_ratio,3),
        "lean_ratio":round(lean_ratio,3),"scale":round(scale,3)
    }

# ----- UI -----
tabs = st.tabs(["Mis datos","Plan nutricional","🔍 Debug % Graso"])

with tabs[0]:
    st.header("Mis datos")
    
    st.info(f"**Referencia:** Peso {st.session_state.user.get('template_weight')}kg, Grasa {st.session_state.user.get('template_fat')}%")
    
    c1,c2 = st.columns(2)
    with c1:
        peso = st.number_input("Peso actual (kg)", value=float(st.session_state.user["peso"]), step=0.1)
        altura = st.number_input("Altura (cm)", value=int(st.session_state.user["altura_cm"]), step=1)
    with c2:
        grasa = st.number_input("Grasa actual (%)", value=float(st.session_state.user["grasa_pct"]), step=0.1)
        objetivo = st.selectbox("Objetivo", ["Recomposición","Volumen","Definición"], 
                              index=["Recomposición","Volumen","Definición"].index(st.session_state.user["objetivo"]))
    
    if st.button("💾 Actualizar datos", type="primary"):
        st.session_state.user.update({
            "peso": float(peso), "altura_cm": int(altura), 
            "grasa_pct": float(grasa), "objetivo": objetivo
        })
        st.success("✅ Datos actualizados")
        st.rerun()

with tabs[1]:
    st.header("Plan nutricional")
    user = st.session_state.user
    
    # ✅ CALCULO QUE SÍ DEPENDE DEL % GRASO
    targets = compute_targets(user, user["objetivo"], "Gimnasio")
    
    st.write(f"**Peso:** {user['peso']}kg | **Grasa:** {user['grasa_pct']}%")
    st.write(f"**Masa magra:** {targets['lean_kg']}kg | **Proteína/kg:** {targets['prot_per_kg_lean']}g")
    st.write(f"**Objetivo:** {user['objetivo']} | **Calorías:** {targets['cal']} kcal")
    st.write(f"**Macros:** P{targets['protein_g']}g / C{targets['carb_g']}g / G{targets['fat_g']}g")
    
    day_choice = st.selectbox("Día", list(TRAINING_WEEK.keys()), key="dia_select")
    day_type = TRAINING_WEEK[day_choice]
    
    targets_day = compute_targets(user, user["objetivo"], day_type)
    
    meal_perc = {"Desayuno":0.25, "Comida":0.35, "Merienda":0.15, "Cena":0.25}
    carb_priority = 1.15 if day_type in ["CrossFit","Halterofilia"] else (0.9 if day_type=="Descanso" else 1.0)

    for meal, perc in meal_perc.items():
        if meal in FOODS:
            meal_cal = int(round(targets_day["cal"] * perc * carb_priority))
            st.subheader(f"{meal} - {meal_cal} kcal")
            
            for i, rec in enumerate(FOODS[meal], 1):
                scaled = escala_final(rec, meal_cal, user)
                st.write(f"**Opción {i}:** {rec['desc']}")
                st.write(f"- Proteína: {scaled['prot_food_g']}g | Carbos: {scaled['carb_crudo_g']}g")
                st.write(f"- Macros: P{scaled['p']}g C{scaled['c']}g G{scaled['f']}g - {scaled['kcal']} kcal")
                st.write("---")

with tabs[2]:
    st.header("🔍 Debug - % Graso SÍ Afecta")
    
    user = st.session_state.user
    
    # TEST con diferentes % graso
    st.subheader("TEST: Cómo afecta el % graso a la proteína")
    
    test_cases = [
        {"grasa": 40, "peso": 92.1},
        {"grasa": 30, "peso": 92.1}, 
        {"grasa": 25, "peso": 92.1},
        {"grasa": 15, "peso": 92.1},
        {"grasa": 10, "peso": 92.1}
    ]
    
    for test in test_cases:
        test_user = user.copy()
        test_user["grasa_pct"] = test["grasa"]
        test_targets = compute_targets(test_user, "Recomposición", "Gimnasio")
        
        st.write(f"**{test['grasa']}% graso:** Masa magra {test_targets['lean_kg']}kg → Proteína {test_targets['protein_g']}g")
    
    st.subheader("Tus datos actuales:")
    st.write(f"- % Graso: {user['grasa_pct']}%")
    st.write(f"- Masa magra: {masa_magra(user):.1f}kg") 
    st.write(f"- Proteína objetivo: {compute_targets(user, user['objetivo'], 'Gimnasio')['protein_g']}g")
    
    # Verificación
    actual_targets = compute_targets(user, user["objetivo"], "Gimnasio")
    if user["grasa_pct"] != DEFAULT["grasa_pct"] and actual_targets["protein_g"] != compute_targets(DEFAULT, user["objetivo"], "Gimnasio")["protein_g"]:
        st.success("✅ CORRECTO: El % graso SÍ está afectando la proteína")
    else:
        st.error("❌ PROBLEMA: El % graso NO afecta la proteína")

st.success("**APP CORREGIDA:** El % graso ahora SÍ afecta proteína e hidratos")
