import streamlit as st
from src.db_connection import get_supabase_client
from datetime import datetime
import pandas as pd
import io
import os
from src.utils.pdf_generator_images import create_percentage_donut
from src.utils.pdf_generator_docx import generate_pdf_from_docx

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
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            btn_save = st.form_submit_button("💾 Guardar y Enviar Evaluación", type="primary", use_container_width=True)
        with col_btn2:
            btn_generate = st.form_submit_button("📄 Generar Anexo 5.4 PDF", type="secondary", use_container_width=True)
        
        if btn_save or btn_generate:
            if not mes_evaluado:
                 st.error("Por favor ingrese el Mes Evaluado.")
            else:
                 # Calculate Average
                 total_grade = sum(eval_data.values())
                 count_acts = len(eval_data)
                 average = int(total_grade / count_acts) if count_acts > 0 else 0
                 
                 if btn_save:
                     try:
                         supabase.table("proyectos_dual").update({"calificacion_ue": average}).eq("id", project_id).execute()
                         st.success(f"Evaluación guardada exitosamente. Promedio preliminar: {average}%")
                     except Exception as e:
                         st.error(f"Error al guardar calificación en base de datos: {e}")
                 
                 if btn_generate:
                     with st.spinner("Generando Documento..."):
                         try:
                             # 1. Generate Donut Chart
                             # We need a temporary physical file to inject into docx
                             chart_path = f"tmp_chart_{student_id}.png"
                             create_percentage_donut(average, chart_path)
                             
                             # 2. Build Context for DOCX
                             context = build_anexo54_context(
                                  project_data,
                                  competencias,
                                  actividades,
                                  eval_data,
                                  mes_evaluado,
                                  numero_reporte,
                                  chart_path,
                                  average
                             )
                             
                             # Ensure templates folder exists
                             templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "docs")
                             os.makedirs(templates_dir, exist_ok=True)
                             template_path = os.path.join(templates_dir, "Anexo_5.4_Reporte_de_Actividades.docx")
                             pdf_path = f"tmp_anexo54_{student_id}.pdf"
                             
                             # Generate PDF using the modular function
                             success, msg = generate_pdf_from_docx(
                                 "Anexo_5.4_Reporte_de_Actividades.docx",
                                 context,
                                 pdf_path,
                                 template_path=template_path
                             )
                             
                             # Cleanup chart
                             if os.path.exists(chart_path):
                                 os.remove(chart_path)
                                 
                             # Show Download Button
                             if success and os.path.exists(pdf_path):
                                 st.success("¡Documento Anexo 5.4 generado exitosamente!")
                                 with open(pdf_path, "rb") as f:
                                     doc_bytes = f.read()
                                 
                                 file_name = f"Anexo_5.4_{alumno['matricula']}_{mes_evaluado.replace(' ', '_')}.pdf"
                                 st.download_button(
                                     label="📥 Descargar Anexo 5.4 (PDF)",
                                     data=doc_bytes,
                                     file_name=file_name,
                                     mime="application/pdf",
                                     type="primary"
                                 )
                                 os.remove(pdf_path) # Cleanup temp pdf
                             else:
                                 st.error(f"No se pudo generar el documento: {msg}")
                         except Exception as e:
                             st.error(f"Error generando documento: {e}")
                             # cleanup chart on crash
                             if 'chart_path' in locals() and os.path.exists(chart_path):
                                  os.remove(chart_path)
                             if 'pdf_path' in locals() and os.path.exists(pdf_path):
                                  os.remove(pdf_path)

    if st.button("Cancelar / Volver"):
         del st.session_state["evaluating_student_id"]
         del st.session_state["eval_project_id"]
         st.rerun()

def build_anexo54_context(project_data, competencias, actividades, eval_data, mes_evaluado, numero_reporte, chart_path, average):
    """
    Constructs the exact dictionary mapping required by the Anexo 5.4 Word Template.
    """
    from docxtpl import InlineImage
    import docx
    
    # Needs a dummy doc object for InlineImage, python-docx handles this
    # Actually, InlineImage takes the template doc as first arg inside python-docx/docxtpl
    # But usually creating InlineImage happens at render time, so we wrap it inside generate function?
    # No, python-docx/docxtpl InlineImage takes (tpl, image_descriptor) 
    # To bypass needing 'tpl' here, docxtpl allows `docxtpl.InlineImage(tpl, path)` 
    # Wait, I don't have `tpl` here.
    # SOLUTION: I will pass chart_path as a string 'IMAGE_PATH:tmp_chart.png' and let
    # `pdf_generator_docx.py` handle converting it to InlineImage before rendering.
    
    a = project_data["alumnos"]
    emp = project_data.get("unidades_economicas", {})
    m_ue = project_data.get("mentores_ue", {})
    
    # We need mentor IE info. It's stored as mentor_ie_id in project. We need to fetch it.
    supabase = get_supabase_client()
    m_ie_name = "N/A"
    m_ie_tel = ""
    if project_data.get("mentor_ie_id"):
        res_mie = supabase.table("maestros").select("nombre_completo, telefono").eq("id", project_data["mentor_ie_id"]).execute()
        if res_mie.data:
            m_ie_name = res_mie.data[0]["nombre_completo"]
            m_ie_tel = res_mie.data[0].get("telefono", "")
            
    # Also fetch Carrera name
    c_name = "N/A"
    if a.get("carrera_id"):
         res_c = supabase.table("carreras").select("nombre").eq("id", a["carrera_id"]).execute()
         if res_c.data:
              c_name = res_c.data[0]["nombre"]

    context = {
        "numero_reporte": numero_reporte,
        "fechas_periodo": mes_evaluado, # The period evaluated
        "nombre_proyecto": project_data.get("nombre_proyecto", ""),
        "empresa": emp.get("nombre_comercial", ""),
        "institucion_educativa": "Tecnológico de Estudios Superiores de Ecatepec",
        "carrera": c_name,
        "nombre_alumno": f"{a['nombre']} {a['ap_paterno']} {a['ap_materno']}",
        "telefono_alumno": a.get("telefono", ""),
        "mentor_ue": m_ue.get("nombre_completo", ""),
        "telefono_mentorue": m_ue.get("telefono", ""),
        "mentor_ie": m_ie_name,
        "telefono_mentorie": m_ie_tel,
        "fecha_elaboracion": datetime.now().strftime("%d/%m/%Y"),
        # The chart path string. The generator must intercept this and convert to InlineImage
        "grafica_promedio": f"IMAGE_PATH:{chart_path}" 
    }
    
    # B) Tabla 2.- Desarrollo de Competencia
    lista_competencias = []
    
    # C) Tabla 3.- Evaluación de la UE (Matrices repetibles)
    evaluaciones = []
    
    for i, comp in enumerate(competencias):
         comp_acts = [act for act in actividades if act["competencia_id"] == comp["id"]]
         if not comp_acts: continue
         
         # Build List for Table 2
         lista_competencias.append({
             "numero_consecutivo": i + 1,
             "competencia_desarrollada": comp["descripcion_competencia"],
             "asignaturas_cubre": comp["asignaturas"]["nombre"]
         })
         
         # Build Matrix for Table 3
         eval_matrix = {
             "competencia_alcanzada": comp["descripcion_competencia"], # User said no sequence number needed now
             "firma_y_fecha": f"{m_ue.get('nombre_completo', '')}\n{datetime.now().strftime('%d/%m/%Y')}",
             "actividades": []
         }
         
         for act in comp_acts:
              g = eval_data.get(act["id"], 0)
              act_dict = {
                  "descripcion_actividad": act["descripcion_actividad"],
                  "evidencia": act.get("evidencia", ""),
                  "horas": act.get("horas_dedicacion", 0),
                  "p0": "X" if g == 0 else "",
                  "p70": "X" if g == 70 else "",
                  "p80": "X" if g == 80 else "",
                  "p90": "X" if g == 90 else "",
                  "p100": "X" if g == 100 else "",
                  "rec_ie": "", # Leave blank for Mentor IE to fill physically or next step? Format implies empty.
                  "rec_ue": ""  # User said "ya la matriz no lleva recomendacion ue ni ie" - I will omit these rows per latest screenshot.
              }
              eval_matrix["actividades"].append(act_dict)
              
         evaluaciones.append(eval_matrix)

    context["lista_competencias"] = lista_competencias
    context["evaluaciones"] = evaluaciones
    
    return context
