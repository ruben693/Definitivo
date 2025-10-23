# Agente de Nutrición Deportiva — V11 Pro (Final)

Versión final: ajusta **gramos de comida** automáticamente según:
- Masa magra (peso y %grasa)
- Objetivo (Recomposición / Volumen / Definición)
- Día de entrenamiento (CrossFit / Halterofilia / Gimnasio / Descanso)

## Archivos
- app_v11_pro.py
- requirements.txt
- README.md

## Cómo desplegar (Streamlit Cloud)
1. Sube los 3 archivos a tu repo (ej. nutricion_recomposicion_definitiva).
2. En https://share.streamlit.io → New app → selecciona repo → Branch `main` → Main file path `app_v11_pro.py` → Deploy.
3. Abre la app y en "Mis datos corporales" pulsa **Guardar y actualizar** antes de ver el plan.

## Qué comprobar (tests rápidos)
1. En "Mis datos corporales" deja valores iniciales y pulsa Guardar.
2. Ve a "Plan nutricional" — observa porciones (prot alimento g, carb crudo/cocido, huevos/claras).
3. Cambia objetivo a Volumen → las porciones deben aumentar.
4. Cambia objetivo a Definición → las porciones deben disminuir.
5. Cambia Peso (por ejemplo 92.1 → 90) y pulsa Guardar → las porciones deben disminuir proporcionalmente.
6. Selecciona día CrossFit/Halterofilia → los hidratos aumentan relativamente.

## Notas técnicas
- Escalado usado: combinación de ratio kcal objetivo / kcal plantilla y ratio masa magra actual / masa magra plantilla.
- Seguridad: calorías no inferiores a 1.05×BMR.
- Guarda siempre antes de ver el plan para aplicar cambios.

## Recomendación
- Registra entrada semanal para mantener historial y ver gráficas.
- Para producción: añadir autenticación y base de datos para multiusuario.
