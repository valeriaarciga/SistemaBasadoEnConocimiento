import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(
    page_title="Medical Diagnosis",
    page_icon="⚕️",
    layout="centered"
)

# CSS personalizado
st.markdown("""
    <style>
    /* Estilos principales */
    .main-header {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
    }
    
    .diagnosis-card {
        padding: 1rem;
        border-left: 4px solid #1E88E5;
        margin: 1rem 0;
        background: #F8F9FA;
    }
    
    /* Botones y progreso */
    button {
        background: #1E88E5 !important;
        color: white !important;
        border-radius: 5px;
    }
    
    .stProgress > div > div > div {
        background: #1E88E5 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('Diagnostico_basado_en_reglas.csv')
    return df

df = load_data()
label_col = 'diseases'
symptom_cols = [col for col in df.columns if col != label_col]
grouped = df.groupby(label_col)[symptom_cols].sum()
cases_per_disease = df[label_col].value_counts()
THRESHOLD = 0.33

# Cálculo de coincidencias
def calculate_match_score(disease, selected_symptoms):
    disease_symptoms = grouped.loc[disease]
    disease_symptoms_set = set(disease_symptoms[disease_symptoms >= THRESHOLD].index)
    selected_set = set(selected_symptoms)
    return len(selected_set.intersection(disease_symptoms_set)) / len(selected_set) if selected_set else 0


"""Funciones no implementadas"""
# Obtención de mejor síntoma para preguntar
def best_symptom(candidates, asked):
    sub = grouped.loc[candidates]
    freqs = sub.div(cases_per_disease[candidates], axis=0)
    best_sym = None
    best_score = -1
    for sym in symptom_cols:
        if sym in asked:
            continue
        has_sym = freqs[sym] >= THRESHOLD
        p = has_sym.mean()
        score = 1 - abs(0.5 - p)
        if score > best_score:
            best_score = score
            best_sym = sym
    return best_sym

# Actualización de enfermedades posibles
def update_candidates(candidates, symptom, has_symptom):
    sub = grouped.loc[candidates]
    freqs = sub.div(cases_per_disease[candidates], axis=0)
    if has_symptom:
        filtered = freqs.index[freqs[symptom] >= THRESHOLD].tolist()
    else:
        filtered = freqs.index[freqs[symptom] < THRESHOLD].tolist()
    return filtered if filtered else []

# Obtención de síntoma específico
def find_specific_symptom(candidates, asked):
    sub = grouped.loc[candidates]
    freqs = sub.div(cases_per_disease[candidates], axis=0)
    specificity = {}
    for sym in symptom_cols:
        if sym in asked:
            continue
        vals = freqs[sym]
        specificity[sym] = vals.max() - vals.min()
    return max(specificity, key=specificity.get) if specificity else None

# Interfaz de usuario
st.markdown("""
    <div class="main-header">
        <h1>⚕️ Medical Diagnosis Assistant</h1>
        <p>Developed by: Abril Álvarez & Valeria Arciga</p>
    </div>
""", unsafe_allow_html=True)

# Personalización con nombre del paciente
with st.form("diagnosis_form"):
    patient_name = st.text_input("Patient Name:", placeholder="Write your name...")
    selected_symptoms = st.multiselect(
        "Select Symptoms:",
        options=symptom_cols,
        placeholder="You can search and select multiple symptoms",
    )
    # Botón de análisis
    submitted = st.form_submit_button("Analyze Symptoms")

# Procesamiento de diagnóstico
if submitted:
    if not patient_name or not selected_symptoms:
        st.warning("Please complete all fields")
    else:
        with st.spinner("Analyzing symptoms..."):
            scores = []
            for disease in grouped.index:
                score = calculate_match_score(disease, selected_symptoms)
                if score > 0:
                    scores.append((disease, score))
            
            if not scores:
                st.error("No matches found")
            else:
                scores.sort(key=lambda x: x[1], reverse=True)
                
                # Resultado principal
                st.markdown(f"""
                    <div class="diagnosis-card">
                        <h3>Primary Diagnosis</h3>
                        <h2>{scores[0][0]}</h2>
                        <p>Patient: {patient_name}</p>
                        <p>Confidence: {scores[0][1]:.0%}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Otros diagnósticos
                if len(scores) > 1:
                    st.subheader("Other Possible Diagnoses")
                    cols = st.columns(2)
                    for i, (disease, score) in enumerate(scores[1:3], 1):
                        with cols[i-1]:
                            st.write(f"**{i}. {disease}**")
                            st.progress(score, text=f"{score:.0%} Match")

# Botón de reinicio
if st.button("🔄 Reset Diagnosis"):
    st.session_state.clear()
    st.rerun()