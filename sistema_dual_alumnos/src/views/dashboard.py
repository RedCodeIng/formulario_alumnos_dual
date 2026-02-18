
import streamlit as st
from src.components.cards import get_card_html
from src.db_connection import get_supabase_client
import pandas as pd
from src.utils.assignment import assign_mentors_round_robin

def render_dashboard():
    st.title("Panel de Control - Coordinador DUAL")
    st.markdown("---")
    
    # KPI Cards Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(get_card_html("Alumnos Registrados", "50", "fas fa-user-graduate"), unsafe_allow_html=True)
    with col2:
        st.markdown(get_card_html("Empresas Activas", "12", "fas fa-building", color="#a48857"), unsafe_allow_html=True)
    with col3:
        st.markdown(get_card_html("Mentores IE", "8", "fas fa-chalkboard-teacher"), unsafe_allow_html=True)
    with col4:
        st.markdown(get_card_html("Documentos Gen.", "150", "fas fa-file-alt", color="#a48857"), unsafe_allow_html=True)

    st.markdown("---")
    
    tab_alumnos, tab1, tab2, tab3, tab4 = st.tabs(["Alumnos DUAL", "Asignaturas", "Maestros", "Unidades Económicas", "Operaciones Académicas"])
    
    supabase = get_supabase_client()
    
    with tab_alumnos:
        st.header("Listado Maestro de Alumnos")
        
        # Load Students joined with Projects and Mentors IE
        # Supabase join syntax: select(*, proyectos_dual(*))
        # For simplicity, we fetch tables independently and merge in pandas if needed, or use specific query
        res_alumnos = supabase.table("alumnos").select("*").execute()
        
        if res_alumnos.data:
            df_alumnos = pd.DataFrame(res_alumnos.data)
            
            # Allow basic filtering
            st.dataframe(
                df_alumnos, 
                column_config={
                    "matricula": "Matrícula",
                    "nombre": "Nombre",
                    "ap_paterno": "Apellido P.",
                    "carrera": "Carrera",
                    "email_institucional": "Email"
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.info("Selecciona un alumno para ver sus detalles completos (En desarrollo: Vista Detallada).")
        else:
            st.info("No hay alumnos registrados aún.")

    with tab1:
        st.header("Gestión de Asignaturas")
        
        # Load Subjects
        response = supabase.table("asignaturas").select("*").execute()
        df_subjects = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=["clave_asignatura", "nombre", "carrera"])
        
        # Editable Dataframe
        edited_df = st.data_editor(df_subjects, num_rows="dynamic", key="subjects_editor")
        
        if st.button("Guardar Cambios Asignaturas"):
            st.warning("Funcionalidad de guardado masivo en desarrollo.")
        
    with tab2:
        st.header("Gestión de Maestros")
        
        with st.expander("Registrar Nuevo Maestro"):
            with st.form("new_teacher"):
                clave = st.text_input("Clave Maestro")
                nombre = st.text_input("Nombre Completo")
                email = st.text_input("Email Institucional")
                es_mentor = st.checkbox("¿Es Mentor IE?")
                division = st.selectbox("División", ["Sistemas", "Industrial", "Mecánica", "Gestión Empresarial"])
                
                submitted = st.form_submit_button("Registrar")
                if submitted:
                    new_teacher = {
                        "clave_maestro": clave,
                        "nombre_completo": nombre,
                        "email_institucional": email,
                        "es_mentor_ie": es_mentor
                    }
                    try:
                        res = supabase.table("maestros").insert(new_teacher).execute()
                        st.success("Maestro registrado correctamente.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        # List Teachers
        res_teachers = supabase.table("maestros").select("*").execute()
        if res_teachers.data:
            st.dataframe(res_teachers.data, use_container_width=True)
        
    with tab3:
        st.header("Directorio de Unidades Económicas (Empresas)")
        
        with st.expander("Registrar Nueva UE"):
            with st.form("new_ue"):
                nombre_com = st.text_input("Nombre Comercial")
                razon = st.text_input("Razón Social")
                rfc = st.text_input("RFC")
                direccion = st.text_input("Dirección Fiscal")
                
                submitted_ue = st.form_submit_button("Registrar Empresa")
                if submitted_ue:
                    new_ue = {
                        "nombre_comercial": nombre_com,
                        "razon_social": razon,
                        "rfc": rfc,
                        "direccion": direccion
                    }
                    try:
                        supabase.table("unidades_economicas").insert(new_ue).execute()
                        st.success("Empresa registrada.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Load UEs
        res_ues = supabase.table("unidades_economicas").select("*").execute()
        if res_ues.data:
            st.dataframe(res_ues.data, use_container_width=True)

    with tab4:
        st.header("Operaciones Académicas (Automatización)")
        
        col_ops1, col_ops2 = st.columns(2)
        
        with col_ops1:
            st.subheader("Asignación de Mentores IE")
            st.write("Asignar mentores académicos automáticamente usando Round Robin.")
            
            if st.button("Ejecutar Asignación Automática"):
                with st.spinner("Asignando mentores..."):
                    success, msg = assign_mentors_round_robin()
                    if success:
                        st.success(msg)
                    else:
                        st.error(f"Error: {msg}")

        with col_ops2:
            st.subheader("Generación Masiva de Documentos")
            st.write("Generar Anexo 5.1 y Carta de Asignación para todos los alumnos asignados y enviar por correo.")
            
            if st.button("Generar y Enviar Documentación"):
                st.info("Iniciando proceso por lotes (Demo)...")
                
                # Demo logic to simulate generation and sending
                # In real scenario, we would iterate over assigned students
                
                progress_bar = st.progress(0)
                import time
                
                # Simulated steps
                for i in range(100):
                    time.sleep(0.05)
                    progress_bar.progress(i + 1)
                
                st.success("Proceso completado.")
