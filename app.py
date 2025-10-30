import streamlit as st

st.set_page_config(layout="centered")
st.title("🏋️ Nutrición - CORREGIDO")

# Estado
if "user" not in st.session_state:
    st.session_state.user = {
        "peso": 92.1, "grasa_pct": 37.9, "objetivo": "Recomposición",
        "template_weight": 92.1, "template_fat": 37.9
    }

# Pestañas
tab1, tab2, tab3 = st.tabs(["📊 Datos", "🍽️ Comida", "🔍 Debug"])

with tab1:
    st.header("Mis Datos")
    
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso (kg)", value=st.session_state.user["peso"], step=0.1)
    with col2:
        grasa = st.number_input("Grasa (%)", value=st.session_state.user["grasa_pct"], step=0.1)
    
    objetivo = st.selectbox("Objetivo", ["Recomposición","Volumen","Definición"])
    
    if st.button("💾 Guardar"):
        st.session_state.user.update({
            "peso": peso, "grasa_pct": grasa, "objetivo": objetivo
        })
        st.success("✅ Guardado!")
        st.rerun()

with tab2:
    st.header("Plan de Comida")
    
    user = st.session_state.user
    
    # Cálculo que SÍ depende del % graso
    def masa_magra(u):
        return u["peso"] * (1 - u["grasa_pct"]/100.0)
    
    masa_magra_actual = masa_magra(user)
    
    # Proteína según % graso
    if user["grasa_pct"] >= 30:
        proteina_g = int(masa_magra_actual * 2.2)
    elif user["grasa_pct"] < 15:
        proteina_g = int(masa_magra_actual * 1.6)
    else:
        proteina_g = int(masa_magra_actual * 2.0)
    
    st.write(f"**Masa magra:** {masa_magra_actual:.1f}kg")
    st.write(f"**Proteína objetivo:** {proteina_g}g")
    
    # Ejemplo de comida
    pollo_base = 160
    arroz_base = 40
    
    # Escalado por peso
    peso_ratio = user["peso"] / user["template_weight"]
    pollo_ajustado = int(pollo_base * peso_ratio)
    arroz_ajustado = int(arroz_base * peso_ratio)
    
    st.write("**Comida ejemplo:**")
    st.write(f"- Pollo: {pollo_base}g → {pollo_ajustado}g")
    st.write(f"- Arroz: {arroz_base}g → {arroz_ajustado}g")

with tab3:
    st.header("Debug - % Graso")
    
    user = st.session_state.user
    
    st.write("**TEST con diferentes % graso:**")
    
    pesos_grasa = [40, 30, 25, 15, 10]
    
    for grasa_test in pesos_grasa:
        masa_magra_test = user["peso"] * (1 - grasa_test/100.0)
        
        if grasa_test >= 30:
            proteina_test = int(masa_magra_test * 2.2)
        elif grasa_test < 15:
            proteina_test = int(masa_magra_test * 1.6)
        else:
            proteina_test = int(masa_magra_test * 2.0)
        
        st.write(f"- {grasa_test}% graso: {masa_magra_test:.1f}kg magro → {proteina_test}g proteína")
    
    st.write("---")
    st.write("**Tus datos:**")
    st.write(f"- {user['grasa_pct']}% graso")
    st.write(f"- {masa_magra(user):.1f}kg masa magra")

st.success("✅ % Graso SÍ afecta las cantidades")
