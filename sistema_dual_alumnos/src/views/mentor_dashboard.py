import streamlit as st
from src.db_connection import get_supabase_client
from datetime import datetime
import pandas as pd
import io
import os

def render_mentor_dashboard():
    # Enforce Auth
    if not st.session_state.get("authenticated") or st.session_state.get("role") != "mentor_ue":
        st.error("Acceso Denegado. Por favor, inicie sesión como Mentor Empresarial.")
        st.stop()
        
    mentor = st.session_state.get("user")
    ue_name = st.session_state.get("ue_name", "Empresa DUAL")
    
    st.markdown(f"## 🏢 Panel Empresarial: {ue_name}")
    st.markdown(f"**Bienvenido(a):** {mentor.get('nombre_completo')}")
    st.markdown("---")
    
    st.write("### Estudiantes a tu cargo")
    st.info("Selecciona un estudiante para realizar su Evaluación Mensual (Anexo 5.4).")
    
    supabase = get_supabase_client()
    
    # Get active periods to filter students (Optional, but good practice)
    # Using open query. Just get students assigned to this mentor
    try:
        # We join proyectos_dual and alumnos
        res_proyectos = supabase.table("proyectos_dual").select(
            "id, nombre_proyecto, alumno_id, periodo_id, alumnos(matricula, nombre, ap_paterno, ap_materno, carrera_id), periodos(nombre)"
        ).eq("mentor_ue_id", mentor["id"]).execute()
        
        proyectos = res_proyectos.data if res_proyectos.data else []
        
        if not proyectos:
            st.warning("No tienes estudiantes asignados actualmente.")
            return
            
        # Display list of students
        for p in proyectos:
            a = p["alumnos"]
            student_name = f"{a['nombre']} {a['ap_paterno']} {a['ap_materno']}"
            period_name = p["periodos"]["nombre"] if p.get("periodos") else "Actual"
            
            with st.expander(f"🎓 {student_name} - {a['matricula']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Proyecto:** {p['nombre_proyecto']}")
                    st.write(f"**Periodo:** {period_name}")
                with col2:
                    if st.button("Evaluar (Anexo 5.4)", key=f"eval_{p['alumno_id']}"):
                        # Redirect to evaluation form
                        st.session_state["evaluating_student_id"] = p["alumno_id"]
                        st.session_state["eval_project_id"] = p["id"]
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Error al cargar estudiantes: {e}")

    # Render Evaluation Form if selected
    if st.session_state.get("evaluating_student_id"):
        st.markdown("---")
        render_evaluation_form()

def render_evaluation_form():
    st.subheader("Evaluación Mensual del Estudiante (Anexo 5.4)")
    student_id = st.session_state.get("evaluating_student_id")
    project_id = st.session_state.get("eval_project_id")
    
    supabase = get_supabase_client()
    
    # 1. Fetch Student and Project info
    try:
        res_proj = supabase.table("proyectos_dual").select(
            "*, alumnos(*), unidades_economicas(*), mentores_ue(*), periodos(*)"
        ).eq("id", project_id).execute()
        
        if not res_proj.data:
            st.error("No se encontró la información del proyecto.")
            if st.button("Volver"):
                del st.session_state["evaluating_student_id"]
                st.rerun()
            return
            
        project_data = res_proj.data[0]
        alumno = project_data["alumnos"]
        carrera_id = alumno["carrera_id"]
        
        # 2. Fetch Assigned Subjects directly related to this student's current period
        # But DUAL system might just fetch all enrolled subjects for the period
        res_insc = supabase.table("inscripciones_asignaturas").select(
             "asignaturas(id, clave_asignatura, nombre)"
        ).eq("alumno_id", student_id).eq("periodo_id", project_data["periodo_id"]).execute()
        
        if not res_insc.data:
            st.warning("El estudiante no tiene asignaturas registradas en este periodo. No se pueden cargar competencias.")
            if st.button("Volver"):
                del st.session_state["evaluating_student_id"]
                st.rerun()
            return
            
        asignatura_ids = [item["asignaturas"]["id"] for item in res_insc.data if item.get("asignaturas")]
        
        # 3. Fetch Competencias and Actividades for those subjects
        res_comp = supabase.table("asignatura_competencias").select(
             "*, asignaturas(nombre)"
        ).in_("asignatura_id", asignatura_ids).execute()
        
        competencias = res_comp.data if res_comp.data else []
        
        if not competencias:
            st.warning("Las asignaturas del estudiante no tienen competencias registradas en el mapa curricular.")
            if st.button("Volver"):
                del st.session_state["evaluating_student_id"]
                st.rerun()
            return
            
        competencia_ids = [c["id"] for c in competencias]
        res_act = supabase.table("actividades_aprendizaje").select("*").in_("competencia_id", competencia_ids).execute()
        actividades = res_act.data if res_act.data else []
        
    except Exception as e:
        st.error(f"Error cargando datos de evaluación: {e}")
        return

    st.write(f"**Evaluando a:** {alumno['nombre']} {alumno['ap_paterno']} {alumno['ap_materno']}")
    st.write("Por favor, asigne una calificación (Nivel de Desempeño) a cada actividad realizada por el estudiante.")
    st.markdown("---")
    
    # Form UI
    with st.form("eval_form"):
        # We will collect grades in a dictionary: act_id -> grade (0, 70, 80, 90, 100)
        eval_data = {}
        
        for comp in competencias:
            st.markdown(f"#### Competencia {comp['numero_competencia']}: {comp['descripcion_competencia']}")
            st.caption(f"Asignatura: {comp['asignaturas']['nombre']}")
            
            comp_acts = [a for a in actividades if a["competencia_id"] == comp["id"]]
            
            if not comp_acts:
                 st.info("Sin actividades registradas para esta competencia.")
            
            for act in comp_acts:
                 st.markdown(f"**Actividad:** {act['descripcion_actividad']}")
                 
                 col1, col2 = st.columns([1, 2])
                 with col1:
                     st.write(f"**Evidencia:** {act.get('evidencia', 'N/A')}")
                     st.write(f"**Horas:** {act.get('horas_dedicacion', 0)}")
                 with col2:
                     grade = st.radio(
                         "Nivel de Desempeño",
                         options=[0, 70, 80, 90, 100],
                         index=0,
                         horizontal=True,
                         key=f"grade_{act['id']}"
                     )
                     eval_data[act['id']] = grade
            st.markdown("---")
            
        # Common fields
        col_f1, col_f2 = st.columns(2)
        with col_f1:
             mes_evaluado = st.text_input("Mes Evaluado (ej. Octubre 2026)")
        with col_f2:
             numero_reporte = st.number_input("Número de Reporte", min_value=1, value=1)
             
        # Submit actions
        btn_save = st.form_submit_button("💾 Guardar Evaluación", type="primary", use_container_width=True)
        
        if btn_save:
            if not mes_evaluado:
                 st.error("Por favor ingrese el Mes Evaluado.")
            else:
                 # Calculate Average
                 total_grade = sum(eval_data.values())
                 count_acts = len(eval_data)
                 average = int(total_grade / count_acts) if count_acts > 0 else 0
                 
                 try:
                     supabase.table("proyectos_dual").update({"calificacion_ue": average}).eq("id", project_id).execute()
                     st.success(f"Evaluación guardada exitosamente. Promedio preliminar: {average}%")
                     st.info("El Coordinador Institucional ahora podrá visualizar y generar el Anexo 5.4 oficial desde su panel.")
                 except Exception as e:
                     st.error(f"Error al guardar calificación en base de datos: {e}")

    if st.button("Cancelar / Volver"):
         del st.session_state["evaluating_student_id"]
         del st.session_state["eval_project_id"]
         st.rerun()


