# CENTINELA MÉDICO - VERSIÓN FINAL PARA ENSEÑAR A DOCTORES
# Web para computadora y teléfono. Servidor en internet.
# Cada doctor tiene su instancia independiente.

## Qué incluye esta versión final
1. Ingreso de médico con contraseña fuerte (8+, mayúscula, minúscula, número, símbolo)
2. Pacientes ordenados: ROJA primero, AMARILLA, VERDE, SIN CHEQUEO
3. Ficha por paciente: Historial | Síntomas | Exámenes | Diagnósticos | Recetas
4. Exámenes separados: Laboratorio / Ultrasonidos / Radiografías
   - Cada ultrasonido/radiografía con Interpretación del radiólogo y Estado: Pendiente, Normal, Anormal, Requiere otro estudio
   - Alerta: si es Anormal, paciente aparece con "IMAGEN ANORMAL - Revisar" y contador en panel
5. Chequeo automático con 3 probabilidades y urgencia
6. Recetas escritas por el médico + botón Descargar receta para el paciente
7. Agenda de Citas por día, con rojos destacados, aviso si rojo no tiene cita
8. Exportar respaldo JSON

## Cómo entregar a otro doctor (independiente)
- Copiar toda la carpeta
- Cambiar CENTINELA_INSTANCE_ID a doctor-nombre-002
- Borrar backend/centinela.db para que empiece en cero
- Subirlo a su propio servidor (Render / Railway)
- Sus pacientes NUNCA aparecen en tu instancia.

## Cómo correr
pip install flask flask-cors werkzeug
python backend/app.py
Abrir http://localhost:5000

## Aviso
Versión educativa avanzada. No es dispositivo médico certificado. Diagnósticos probables simulados, deben ser validados por el médico. Recetas las escribe el médico.
