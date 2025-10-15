import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Agente Nutrición V8", layout="centered")

st.title("🏋️‍♂️ Agente de Nutrición Deportiva — V8 (Final)")
st.markdown("Recomposición por defecto. 4 comidas al día, alternativas y cantidades reales (crudo/cocido).")

# --- Defaults from your data (baseline) ---
DEFAULTS = {
    "peso": 92.1,
    "imc": 27.2,
    "grasa_pct": 37.9,
    "masa_muscular_kg": 53.2,
    "bmr": 1721.0,
    "altura_cm": 186,
    "edad": 42,
    "sexo": "Masculino",
    "objetivo": "Recomposición"
}

if "user" not in st.session_state:
    st.session_state.user = DEFAULTS.copy()
if "history" not in st.session_state:
    st.session_state.history = []

tab1, tab2, tab3 = st.tabs(["Mis datos corporales", "Plan nutricional", "Evolución"])

# ----------------- Tab: Datos -----------------
with tab1:
    st.header("Mis datos corporales (edítalos y guarda)")
    c1, c2 = st.columns(2)
    with c1:
        peso = st.number_input("Peso (kg)", value=float(st.session_state.user["peso"]), step=0.1)
        imc = st.number_input("IMC", value=float(st.session_state.user["imc"]), step=0.1)
    with c2:
        grasa_pct = st.number_input("Grasa corporal (%)", value=float(st.session_state.user["grasa_pct"]), step=0.1)
        masa_muscular_kg = st.number_input("Masa muscular (kg)", value=float(st.session_state.user["masa_muscular_kg"]), step=0.1)
    b1, b2 = st.columns(2)
    with b1:
        altura_cm = st.number_input("Altura (cm)", value=int(st.session_state.user["altura_cm"]), step=1)
    with b2:
        edad = st.number_input("Edad (años)", value=int(st.session_state.user["edad"]), min_value=15)
    sexo = st.selectbox("Sexo", ["Masculino","Femenino"], index=0 if st.session_state.user.get("sexo","Masculino")=="Masculino" else 1)
    bmr_input = st.number_input("BMR (kcal) (opcional - si tu báscula lo da)", value=float(st.session_state.user.get("bmr", DEFAULTS["bmr"])), step=1.0, format="%.0f")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar y actualizar"):
            st.session_state.user.update({
                "peso": float(peso),
                "imc": float(imc),
                "grasa_pct": float(grasa_pct),
                "masa_muscular_kg": float(masa_muscular_kg),
                "altura_cm": int(altura_cm),
                "edad": int(edad),
                "sexo": sexo,
                "bmr": float(bmr_input)
            })
            st.success("Datos guardados. Ve a 'Plan nutricional' para ver resultados.")
    with col2:
        if st.button("Añadir a historial"):
            st.session_state.history.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "peso": float(peso),
                "grasa_pct": float(grasa_pct),
                "masa_muscular_kg": float(masa_muscular_kg)
            })
            st.success("Entrada añadida al historial.")

# ----------------- Helper funcs -----------------
def mifflin_bmr(user):
    bmr = user.get("bmr",0.0)
    if bmr and bmr>0:
        return float(bmr)
    if user.get("sexo","Masculino")=="Masculino":
        return 10*user["peso"] + 6.25*user["altura_cm"] - 5*user["edad"] + 5
    else:
        return 10*user["peso"] + 6.25*user["altura_cm"] - 5*user["edad"] - 161

def compute_targets(user, objetivo, day_type):
    bmr = mifflin_bmr(user)
    activity_factor = 1.55  # baseline for your weekly activity
    tdee = bmr * activity_factor
    day_mod = {"Gimnasio":1.00, "Intenso":1.10, "Descanso":0.95}
    cal = tdee * (1.15 if objetivo=="Volumen" else (0.8 if objetivo=="Definición" else 1.0)) * day_mod.get(day_type,1.0)
    # protein strategy
    grasa = user.get("grasa_pct",30)
    prot_per_kg = 2.2 if grasa>=30 else (1.8 if grasa<15 else 2.0)
    protein_g = round(prot_per_kg * user["peso"])
    fat_per_kg = 0.9 if objetivo=="Volumen" else (0.7 if objetivo=="Definición" else 0.8)
    fat_g = round(fat_per_kg * user["peso"])
    cal_pf = protein_g*4 + fat_g*9
    carb_g = max(0, round((cal - cal_pf)/4))
    return {"cal": int(round(cal)), "protein_g": int(protein_g), "fat_g": int(fat_g), "carb_g": int(carb_g), "bmr":int(round(bmr)), "tdee":int(round(tdee))}

# ----------------- Tab: Plan -----------------
with tab2:
    st.header("Plan nutricional (4 comidas)")
    st.markdown("Objetivo por defecto: Recomposición. Puedes cambiar objetivo y tipo de día manualmente.")
    c1, c2, c3 = st.columns(3)
    if c1.button("🟩 Volumen"):
        st.session_state.user["objetivo"]="Volumen"
    if c2.button("🟨 Recomposición"):
        st.session_state.user["objetivo"]="Recomposición"
    if c3.button("🟥 Definición"):
        st.session_state.user["objetivo"]="Definición"
    objetivo = st.session_state.user.get("objetivo","Recomposición")
    st.markdown(f"**Objetivo activo:** {objetivo}")

    day_type = st.selectbox("Tipo de día (manual)", ["Gimnasio","Intenso","Descanso"], index=0)
    st.markdown("Semana (referencia): Lun:Gim, Mar:CrossFit, Mié:Descanso, Jue:CrossFit, Vie:Gim, Sáb:Halterofilia, Dom:Descanso")

    # define foods with explicit portion grams for key ingredients (protein and carbs) so we can scale
    # structure: desc, p,g c,g f,g kcal, protein_food_g (protein food grams crudo), carb_crudo_g, carb_cocido_g
    foods = {
        "Desayuno":[
            {"desc":"Avena 60 g + 2 claras + 1 huevo + 1 fruta","p":28,"c":65,"f":9,"kcal":520,"protein_food_g":50,"carb_crudo_g":60,"carb_cocido_g":None},
            {"desc":"Tostadas integrales 80 g + 3 huevos + 1 fruta","p":30,"c":60,"f":15,"kcal":560,"protein_food_g":90,"carb_crudo_g":80,"carb_cocido_g":None},
            {"desc":"Yogur griego 200 g + granola 50 g + fruta","p":22,"c":55,"f":12,"kcal":450,"protein_food_g":200,"carb_crudo_g":50,"carb_cocido_g":None}
        ],
        "Comida":[
            {"desc":"Pechuga pollo 160 g + Arroz 120 g cocido + Verduras","p":45,"c":80,"f":8,"kcal":620,"protein_food_g":160,"carb_crudo_g":40,"carb_cocido_g":120},
            {"desc":"Ternera magra 150 g + Patata 250 g cruda + Verduras","p":44,"c":70,"f":12,"kcal":600,"protein_food_g":150,"carb_crudo_g":250,"carb_cocido_g":420},
            {"desc":"Lomo de cerdo 160 g + Pasta 90 g cruda + Verduras","p":46,"c":85,"f":10,"kcal":650,"protein_food_g":160,"carb_crudo_g":90,"carb_cocido_g":None}
        ],
        "Merienda":[
            {"desc":"Yogur griego 150 g + 25 g nueces","p":18,"c":12,"f":15,"kcal":300,"protein_food_g":150,"carb_crudo_g":25,"carb_cocido_g":None},
            {"desc":"Batido proteína 30 g + 40 g avena","p":30,"c":40,"f":6,"kcal":360,"protein_food_g":30,"carb_crudo_g":40,"carb_cocido_g":None},
            {"desc":"Requesón 150 g + 1 fruta + 20 g semillas","p":20,"c":18,"f":8,"kcal":260,"protein_food_g":150,"carb_crudo_g":None,"carb_cocido_g":None}
        ],
        "Cena":[
            {"desc":"Pescado blanco 180 g + Boniato 150 g crudo + Verduras","p":42,"c":45,"f":8,"kcal":520,"protein_food_g":180,"carb_crudo_g":150,"carb_cocido_g":180},
            {"desc":"Salmón 150 g + Arroz 100 g cocido + Verduras","p":38,"c":50,"f":15,"kcal":600,"protein_food_g":150,"carb_crudo_g":33,"carb_cocido_g":100},
            {"desc":"Tortilla 3 huevos + 100 g patata cocida + Ensalada","p":28,"c":30,"f":18,"kcal":420,"protein_food_g":180,"carb_crudo_g":100,"carb_cocido_g":None}
        ]
    }

    # compute targets
    user = st.session_state.user
    targets = compute_targets(user, objetivo, day_type)
    st.subheader("🔢 Resumen diario")
    st.write(f"BMR usada: **{targets['bmr']} kcal** — TDEE base: **{targets['tdee']} kcal** (factor 1.55)")
    st.write(f"Calorías objetivo (día): **{targets['cal']} kcal**")
    st.write(f"Proteínas: **{targets['protein_g']} g** • Grasas: **{targets['fat_g']} g** • Carbohidratos: **{targets['carb_g']} g**")

    # meal perc (4 meals)
    meal_perc = {"Desayuno":0.25, "Comida":0.35, "Merienda":0.15, "Cena":0.25}

    st.markdown("### Plan diario (4 comidas) — opciones por comida con cantidades escaladas")
    day_for_view = st.selectbox("Selecciona día (informativo)", ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"], index=0)

    for meal, perc in meal_perc.items():
        meal_cal = int(round(targets["cal"]*perc))
        meal_p = int(round(targets["protein_g"]*perc))
        meal_c = int(round(targets["carb_g"]*perc))
        meal_f = int(round(targets["fat_g"]*perc))
        st.markdown(f"**{meal}** — objetivo ~{meal_cal} kcal • P {meal_p}g • C {meal_c}g • F {meal_f}g")
        opts = foods[meal]
        rows = []
        for i,opt in enumerate(opts, start=1):
            # scale each template by kcal ratio
            scale = meal_cal / opt["kcal"] if opt.get("kcal",0)>0 else 1.0
            # limit scale to reasonable range (0.6 - 1.6) to avoid absurd portions
            if scale < 0.6: scale = 0.6
            if scale > 1.6: scale = 1.6
            scaled_p = int(round(opt["p"] * scale))
            scaled_c = int(round(opt["c"] * scale))
            scaled_f = int(round(opt["f"] * scale))
            scaled_kcal = int(round(opt["kcal"] * scale))
            # scale explicit grams where provided
            prot_food_g = opt.get("protein_food_g")
            carb_crudo = opt.get("carb_crudo_g")
            carb_cocido = opt.get("carb_cocido_g")
            prot_food_scaled = int(round(prot_food_g * scale)) if prot_food_g else "-"
            carb_crudo_scaled = int(round(carb_crudo * scale)) if carb_crudo else "-"
            carb_cocido_scaled = int(round(carb_cocido * scale)) if carb_cocido else "-"
            rows.append({
                "Opción": f"Opción {i}",
                "Descripción": opt["desc"],
                "Proteínas (g)": scaled_p,
                "Carbohidratos (g)": scaled_c,
                "Grasas (g)": scaled_f,
                "kcal aprox": scaled_kcal,
                "Prot alimento (g, crudo)": prot_food_scaled,
                "Carb crudo (g)": carb_crudo_scaled,
                "Carb cocido (g)": carb_cocido_scaled
            })
        st.table(pd.DataFrame(rows))

# ----------------- Tab: Evolución -----------------
with tab3:
    st.header("Evolución corporal")
    hist = st.session_state.history
    if len(hist)==0:
        st.info("No hay datos de historial. Usa 'Añadir a historial' en Datos corporales")
    else:
        df = pd.DataFrame(hist)
        st.table(df)
        fig, ax = plt.subplots()
        ax.plot(df['date'], df['peso'], marker='o')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Peso (kg)')
        st.pyplot(fig)
        fig2, ax2 = plt.subplots()
        ax2.plot(df['date'], df['grasa_pct'], marker='o')
        ax2.set_xlabel('Fecha')
        ax2.set_ylabel('Grasa corporal (%)')
        st.pyplot(fig2)

st.markdown("---")
st.markdown("Notas: las porciones son plantillas escaladas automáticamente. Pésalas en crudo donde se indica. Ajusta tus datos para recalibrar el plan.")
