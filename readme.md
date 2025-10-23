# Agente de Nutrición Deportiva — V11 Pro (Final)

Versión final profesional: ajusta **gramos de comida** (crudo/cocido, claras/huevos) automáticamente según:
- Masa magra (peso y %grasa)
- Objetivo (Recomposición / Volumen / Definición)
- Día de entrenamiento (CrossFit / Halterofilia / Gimnasio / Descanso)

## Archivos
- app.py
- requirements.txt
- README.md

## Despliegue en Streamlit Cloud
1. Sube los 3 archivos al repositorio.
2. En https://share.streamlit.io crea New app:
   - Repo: tu usuario / repo
   - Branch: main
   - Main file path: app.py
3. Deploy. Guarda datos en "Mis datos corporales" antes de consultar "Plan nutricional".

## Pruebas rápidas recomendadas
- Guardar datos base (92.1 kg, 37.9%) y comprobar plan.
- Cambiar objetivo a Volumen → porciones aumentan.
- Cambiar objetivo a Definición → porciones disminuyen.
- Cambiar peso (92.1 → 90), Guardar → porciones disminuyen.
- Seleccionar día CrossFit → hidratos aumentan en las comidas.
