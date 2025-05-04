"""Sistema de Diagnostico Basado en Reglas
Valeria Arciga Valencia, Abril Álvarez Mercado

Este sistema utiliza el enfoque basado en reglas y frecuencia de síntomas para realizar un diagnóstico médico preliminar."""

# Importación de librerías
import streamlit as st
import pandas as pd

# Configuración de la interfaz
st.set_page_config(
    page_title="Medical Diagnosis System",
    page_icon="⚕",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS
st.markdown("""
    <style>
    small {
        font-size: 0.9em !important;
    }
    </style>
""", unsafe_allow_html=True)

# Título y descripción
st.markdown("<h1 style='color: #1A237E; text-align: center; margin-bottom: 10px;'>⚕ Medical Diagnosis System</h1>", unsafe_allow_html=True)
st.write("Welcome to the intelligent medical diagnosis system. Please answer the following questions to receive a preliminary analysis.")

# Carga de datos
@st.cache_data
def load_data():
    return pd.read_csv('Diagnostico_basado_en_reglas.csv')

df = load_data()
label_col = 'diseases'
symptom_cols = [col for col in df.columns if col != label_col]
grouped = df.groupby(label_col)[symptom_cols].sum()
cases_per_disease = df[label_col].value_counts()

# Significancia de síntomas
THRESHOLD = 0.3

# Función de síntoma más informativo
def best_symptom(candidates, asked):
    sub = grouped.loc[candidates]
    freqs = sub.div(cases_per_disease[candidates], axis=0)
    best_sym = None
    best_score = -1
    
    for sym in symptom_cols:
        if sym in asked:
            continue

        # Cálculo de probabilidad de relevancia
        has_sym = freqs[sym] >= THRESHOLD
        p = has_sym.mean()

        # Puntuación del síntoma
        score = 1 - abs(0.5 - p)
        if score > best_score:
            best_score = score
            best_sym = sym
    return best_sym

# Filtrado de enfermedades
def update_candidates(candidates, symptom, has_symptom):
    sub = grouped.loc[candidates]
    freqs = sub.div(cases_per_disease[candidates], axis=0)
    if has_symptom:
        filtered = freqs.index[freqs[symptom] >= THRESHOLD].tolist()
    else:
        filtered = freqs.index[freqs[symptom] < THRESHOLD].tolist()
    return filtered

# Función para encontrar síntomas representativos
def find_specific_symptom(candidates, asked):
    sub = grouped.loc[candidates]
    freqs = sub.div(cases_per_disease[candidates], axis=0)
    specificity = {}
    
    for sym in symptom_cols:
        if sym in asked:
            continue
        vals = freqs[sym]

        # Especificidad como diferencia entre máximo y mínimo
        specificity[sym] = vals.max() - vals.min()
    
    if specificity:
        return max(specificity, key=specificity.get)
    return None

# Estado de la sesión
if 'candidates' not in st.session_state:
    st.session_state.candidates = grouped.index.tolist()
    st.session_state.asked = set()
    st.session_state.responses = {}
    st.session_state.prev_candidates = set()
    st.session_state.specific_mode = False

# Flujo de preguntas y respuestas
if len(st.session_state.candidates) > 1 and len(st.session_state.asked) < len(symptom_cols):
    # Selección de la pregunta
    if st.session_state.specific_mode:
        current_symptom = find_specific_symptom(st.session_state.candidates, st.session_state.asked)
    else:
        current_symptom = best_symptom(st.session_state.candidates, st.session_state.asked)

    if current_symptom:
        # Interfaz pregunta
        st.subheader("Do you have this symptom?")
        st.markdown(f"<h3 style='color: #0D47A1;'>{current_symptom.replace('_', ' ').title()}</h3>", unsafe_allow_html=True)
        
        # Botones de respuesta
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ **Yes**", use_container_width=True):
                st.session_state.responses[current_symptom] = True
                st.session_state.asked.add(current_symptom)
                prev = set(st.session_state.candidates)
                st.session_state.candidates = update_candidates(
                    st.session_state.candidates, current_symptom, True
                )
                st.session_state.specific_mode = (set(st.session_state.candidates) == prev)
                st.rerun()
        with col2:
            if st.button("❌ **No**", use_container_width=True):
                st.session_state.responses[current_symptom] = False
                st.session_state.asked.add(current_symptom)
                prev = set(st.session_state.candidates)
                st.session_state.candidates = update_candidates(
                    st.session_state.candidates, current_symptom, False
                )
                st.session_state.specific_mode = (set(st.session_state.candidates) == prev)
                st.rerun()
    else:
        st.session_state.diagnosis_complete = True
        st.rerun()

# Resultados finales
else:
    st.subheader("📋 Final Results")
    st.markdown("---")
    
    # Función para calcular coincidencia
    def calculate_match(disease):
        total_symptoms = 0
        matching = 0
        for sym, answer in st.session_state.responses.items():
            freq = grouped.loc[disease, sym] / cases_per_disease[disease]
            if answer and freq >= THRESHOLD:
                matching += 1
            total_symptoms += 1
        return matching / total_symptoms if total_symptoms > 0 else 0
    
    # Obtener top 3 enfermedades
    if st.session_state.candidates:
        all_candidates = st.session_state.candidates.copy()
        
        # Si hay pocas candidatas, completar con otras
        if len(all_candidates) < 3:
            remaining = [d for d in grouped.index.tolist() if d not in all_candidates]
            all_candidates += remaining[:3-len(all_candidates)]
        
        matches = {disease: calculate_match(disease) for disease in all_candidates}
        top_diseases = sorted(matches.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Diagnóstico principal
        main_diagnosis, main_confidence = top_diseases[0]
        color = "#1E88E5" if main_confidence >= 0.5 else "#FFA000"
        
        st.markdown(f"""
            <div style='border-left: 5px solid {color}; padding: 1.5rem; margin: 2rem 0;
                        background: #F8F9FA; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: {color}; margin-top: 0;'>Primary Diagnosis</h3>
                <h2 style='color: #1A237E; margin: 0.5em 0;'>{main_diagnosis}</h2>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <span style='font-weight: bold; color: {color};'>Match:</span>
                    <span style='background: {color + "20"}; color: {color}; 
                            padding: 2px 10px; border-radius: 20px; font-weight: 500;'>
                        {main_confidence:.0%}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Diagnostico secundario
        if len(top_diseases) > 1:
            st.markdown("#### 📌 Other Possibilities")
            for disease, confidence in top_diseases[1:]:
                st.markdown(f"""
                    <div style='padding: 0.8rem; margin: 0.5rem 0; 
                                background: #E3F2FD; border-radius: 8px;'>
                        <span style='font-weight: 500;'>{disease}</span>
                        <span style='float: right; color: #1E88E5; font-weight: bold;'>{confidence:.0%}</span>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.error("🚨 No matching diagnoses found")

# Botón de reinicio
st.markdown("---")
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("Restart Diagnosis", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()

# Disclaimer
st.markdown("---")
st.markdown("<small>⚠️ This system is a diagnostic support tool. **Does not replace professional medical consultation.**</small>", unsafe_allow_html=True)