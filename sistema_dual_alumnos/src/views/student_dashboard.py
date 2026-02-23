import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
from src.db_connection import get_supabase_client

def render_student_dashboard():
    st.title("Mi Portal DUAL")
    
    user = st.session_state.get("user", {})
    if not user:
        st.error("Sesión no válida.")
        return

    supabase = get_supabase_client()
    
    # FETCH DATA
    # 1. Project
    project = {}
    try:
        res_proj = supabase.table("proyectos_dual").select("*, unidades_economicas(*), mentores_ue(*), maestros(*)").eq("alumno_id", user.get("id")).execute()
        if res_proj.data:
            project = res_proj.data[0]
            # Flatten for easier access if needed, or just use keys
    except Exception as e:
        st.error(f"Error cargando proyecto: {e}")

    # 2. Subjects
    subjects = []
    try:
        # Note: Supabase join syntax might vary depending on client version/setup.
        # Simple approach: fetch IDs and then fetch details if nested select is tricky without ORM
        # But let's try standard PostgREST syntax: select(*, asignaturas(*), maestros(*))
        res_subs = supabase.table("inscripciones_asignaturas").select(
            "*, asignaturas(nombre, clave_asignatura), maestros(nombre_completo)"
        ).eq("alumno_id", user.get("id")).execute()
        
        if res_subs.data:
            subjects = res_subs.data
    except Exception as e:
        st.error(f"Error cargando materias: {e}")

    # Success Box for New Registrations
    if st.session_state.get("registro_complete"):
        st.success("¡Tu registro ha sido completado exitosamente! Ahora puedes ver tu información y estatus.")
        # Optional: Clear the flag so it doesn't show on every refresh, 
        # but for now let's keep it until they logout or for this session.
    
    # UI LAYOUT
    st.markdown(f"### Bienvenido, {user.get('nombre')} {user.get('ap_paterno')}")
    
    tab1, tab2, tab3 = st.tabs(["Mi Información", "Mi Proyecto", "📁 Mis Documentos"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Datos Personales")
            st.write(f"**Matrícula:** {user.get('matricula')}")
            st.write(f"**CURP:** {user.get('curp')}")
            st.write(f"**Email Institucional:** {user.get('email_institucional')}")
            st.write(f"**Teléfono:** {user.get('telefono', 'No registrado')}")
            
        with col2:
            st.markdown("#### Datos Académicos")
            # Robust Career Display
            career_name = st.session_state.get('selected_career') or user.get('carrera') or "Cargando..."
            st.write(f"**Carrera:** {career_name}") 
            st.write(f"**Semestre:** {user.get('semestre')}")
            st.write(f"**Estatus:** {user.get('estatus')}")

        st.markdown("---")
        st.subheader("Carga Académica Actual")
        
        if subjects:
            # Prepare DataFrame for display
            data_rows = []
            for s in subjects:
                asig = s.get("asignaturas", {})
                maestro = s.get("maestros", {})
                data_rows.append({
                    "Clave": asig.get("clave_asignatura", "N/A"),
                    "Asignatura": asig.get("nombre", "N/A"),
                    "Maestro": maestro.get("nombre_completo", "N/A"),
                    "Grupo": s.get("grupo", "N/A"),
                    "P1": "✅" if s.get("parcial_1") else "❌",
                    "P2": "✅" if s.get("parcial_2") else "❌",
                    "P3": "✅" if s.get("parcial_3") else "❌",
                })
            
            st.dataframe(pd.DataFrame(data_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No tienes asignaturas registradas.")

    with tab2:
        if project:
            st.subheader(f"Proyecto: {project.get('nombre_proyecto')}")
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                ue = project.get("unidades_economicas", {})
                mentor = project.get("mentores_ue", {})
                st.write(f"**Empresa:** {ue.get('nombre_comercial', 'N/A')}")
                st.write(f"**Mentor Industrial:** {mentor.get('nombre_completo', 'N/A')}")
            
            with c_p2:
                st.write(f"**Fecha Inicio:** {project.get('fecha_inicio_convenio')}")
                st.write(f"**Fecha Fin:** {project.get('fecha_fin_convenio')}")
            
            st.markdown("#### Descripción del Proyecto")
            st.info(project.get("descripcion_proyecto", "Sin descripción detallada."))
            
        else:
            st.warning("No tienes un proyecto registrado aún.")

    with tab3:
        st.subheader("Estatus de Documentos DUAL")
        st.write("Aquí puedes consultar si cumples con los requisitos para que tu Coordinador genere tus documentos oficiales.")
        
        if not project:
            st.warning("Necesitas tener un Proyecto DUAL registrado y activo para habilitar la generación de documentos.")
            has_project_and_ue = False
            has_mentor_ie = False
            has_all_reqs = False
        else:
            has_project_and_ue = bool(project.get("ue_id") and project.get("mentor_ue_id"))
            has_mentor_ie = bool(project.get("mentor_ie_id"))
            has_all_reqs = has_project_and_ue and has_mentor_ie
            
        st.markdown("---")
        
        def status_card(title, desc, is_ready, ready_msg, missing_msg):
            st.markdown(f"##### {title}")
            st.caption(desc)
            if is_ready:
                st.success(f"🟢 **Completado:** {ready_msg}")
            else:
                st.error(f"🔴 **Pendiente:** {missing_msg}")
            st.markdown("<br>", unsafe_allow_html=True)
            
        c_status1, c_status2 = st.columns(2)
        
        with c_status1:
            status_card(
                "📄 Plan de Formación (Anexo 5.1)",
                "Documento inicial del modelo DUAL con la empresa.",
                has_project_and_ue,
                "Tienes asignada una Empresa y Mentor UE. Tu coordinador puede generar tu anexo.",
                "Falta asignar una Empresa o Mentor UE a tu proyecto."
            )
            
            status_card(
                "✉️ Carta Asignación Mentor IE",
                "Asignación oficial del docente responsable en la institución.",
                has_mentor_ie,
                "Se te ha asignado un Mentor Institucional (IE).",
                "Aún no tienes un Mentor Institucional asignado."
            )
            
        with c_status2:
            status_card(
                "📄 Reportes y Evaluación Final (Anexos 5.4 y 5.5)",
                "Documentos de seguimiento y cierre del modelo.",
                has_all_reqs,
                "Cuentas con asignación completa. Se pueden generar las evaluaciones.",
                "Falta asignación de Empresa/Mentor UE o Mentor Institucional."
            )
            
            status_card(
                "📝 Acta de Calificaciones",
                "Sábana de calificaciones de las asignaturas DUAL.",
                has_all_reqs,
                "El coordinador puede extraer tu acta de calificaciones del periodo.",
                "Falta registro completo de tu proyecto/mentores."
            )
            
        st.info("ℹ️ **Nota:** Para solicitar cualquiera de estos documentos en formato físico o digital con firmas, por favor acércate a la Coordinación DUAL de tu carrera.")
