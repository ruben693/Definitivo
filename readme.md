# Agente de Nutrición Deportiva — V10 Óptimo

Versión final optimizada para ajustar cantidades de comida en función de:
- Masa magra (peso y %grasa)
- Objetivo (Recomposición / Volumen / Definición)
- Día de entrenamiento (CrossFit / Halterofilia / Gimnasio / Descanso)

## Archivos
- app_v10_optimo.py
- requirements.txt
- README.md

## Cómo desplegar
1. Sube los tres archivos al repositorio (ej. `nutricion_recomposicion_definitiva`).
2. En Streamlit Cloud: New app → selecciona repo → branch `main` → Main file path: `app_v10_optimo.py` → Deploy.
3. Guarda datos en "Mis datos corporales" antes de ver el plan (botón "Guardar y actualizar").

## Qué comprobar
- Cambia objetivo (Recomposición → Volumen → Definición): **las porciones deben variar claramente**.
- Cambia peso (ej. 92.1 → 90) y guarda → **porciones disminuyen**.
- Selecciona días intensos (CrossFit / Halterofilia) → **aumentan hidratos** en las tablas.
- Añade historial y revisa las gráficas en "Evolución".

## Nota
- Escalado = (kcal_objetivo / kcal_template) × (masa_magra_actual / masa_magra_template).
- Seguridad: no dejar calorías por debajo de 1.05×BMR.
