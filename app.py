import streamlit as st
st.title("🏋️ Nutrición Simple")
st.write("¡Funciona!")

if "p" not in st.session_state:
    st.session_state.p = 92.1

p = st.number_input("Peso", st.session_state.p)
g = st.number_input("Grasa", 37.9)

if st.button("Guardar"):
    st.session_state.p = p
    st.success(f"Guardado: {p}kg, {g}% grasa")

st.write(f"Masa magra: {p*(1-g/100):.1f}kg")
