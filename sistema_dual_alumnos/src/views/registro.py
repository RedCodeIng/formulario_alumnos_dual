
import streamlit as st
from datetime import date, datetime
from src.utils.helpers import calculate_age, sanitize_input

from src.utils.helpers import calculate_age, sanitize_input
from src.utils.db_actions import create_student_transaction
import re

def render_registro():
    st.title("Inscripción al Modelo DUAL")
    supabase = get_supabase_client()
    
    # 0. Check Status (Prevent Re-registration)
    request_user = st.session_state.get("user", {})
    matricula = request_user.get("matricula", "")
    curp = request_user.get("curp", "")
    
    # Wizard Progress
    step = st.session_state.get("registro_step", 1)
    st.progress(step / 4)
    
    
    if step == 1:
        st.subheader("Datos Personales")
        
        # REMOVED FORM to allow dynamic Age Calculation
        col1, col2 = st.columns(2)
        with col1:
             st.text_input("Matrícula", value=matricula, disabled=True)
             nombre = st.text_input("Nombre(s)", value=str(request_user.get("nombre", "") or ""))
             ap_paterno = st.text_input("Apellido Paterno", value=str(request_user.get("ap_paterno", "") or ""))
             ap_materno = st.text_input("Apellido Materno", value=str(request_user.get("ap_materno", "") or ""))
             
             # Gender and Status
             gen_idx = ["Hombre", "Mujer", "Otro"].index(request_user.get("genero", "Hombre")) if request_user.get("genero") in ["Hombre", "Mujer", "Otro"] else 0
             genero = st.selectbox("Género", ["Hombre", "Mujer", "Otro"], index=gen_idx)
             
             ec_idx = ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"].index(request_user.get("estado_civil", "Soltero/a")) if request_user.get("estado_civil") in ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"] else 0
             estado_civil = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"], index=ec_idx)

        with col2:
             st.text_input("CURP", value=curp, disabled=True)
             nss = st.text_input("Número de Seguridad Social (NSS)", value=str(request_user.get("nss", "") or ""))
             
             # Dates
             min_dob = date(1950, 1, 1)
             max_dob = date(2020, 12, 31)
             default_dob = date(2000, 1, 1)
             
             # Handle previous value if exists
             prev_dob = request_user.get("fecha_nacimiento")
             if isinstance(prev_dob, str):
                 try:
                     prev_dob = datetime.strptime(prev_dob, "%Y-%m-%d").date()
                 except:
                     prev_dob = default_dob
             
             fecha_nac = st.date_input("Fecha de Nacimiento", value=prev_dob if prev_dob else default_dob, min_value=min_dob, max_value=max_dob)
             
             # DYNAMIC CALCULATION
             edad = calculate_age(fecha_nac)
             st.info(f"Edad calculada: {edad} años")
             
             email_inst = st.text_input("Correo Institucional", value=str(request_user.get("email_institucional", "") or ""))
             email_pers = st.text_input("Correo Personal", value=str(request_user.get("email_personal", "") or ""))
             telefono = st.text_input("Teléfono", value=str(request_user.get("telefono", "") or ""))

        st.markdown("---")
        st.subheader("Datos Académicos")
        col_aca1, col_aca2 = st.columns(2)
        
        # Get Context
        selected_career_name = st.session_state.get("selected_career", "Carrera no designada")
        selected_career_id = st.session_state.get("selected_career_id", None)
        
        with col_aca1:
            st.text_input("Carrera", value=selected_career_name, disabled=True)
            
        with col_aca2:
            sem_idx = ["6", "7", "8", "9"].index(request_user.get("semestre", "6")) if request_user.get("semestre") in ["6", "7", "8", "9"] else 0
            semestre = st.selectbox("Semestre", ["6", "7", "8", "9"], index=sem_idx)
        
        if st.button("Siguiente >"):
            # Sanitize Personal Data
            nombre = sanitize_input(nombre)
            ap_paterno = sanitize_input(ap_paterno)
            ap_materno = sanitize_input(ap_materno)
            email_inst = sanitize_input(email_inst)
            email_pers = sanitize_input(email_pers)
            telefono = sanitize_input(telefono)
            nss = sanitize_input(nss)

            if not nombre or not ap_paterno or not nss or not email_inst or not email_pers or not telefono:
                    st.error("Por favor llene todos los campos obligatorios.")
            elif not selected_career_id:
                    st.error("Error crítico: No se ha detectado su carrera. Por favor vuelva a iniciar sesión.")
            else:
                request_user.update({
                    "nombre": nombre, "ap_paterno": ap_paterno, "ap_materno": ap_materno,
                    "nss": nss, "fecha_nacimiento": fecha_nac,
                    "genero": genero, "estado_civil": estado_civil,
                    "email_institucional": email_inst, "email_personal": email_pers, "telefono": telefono,
                    "carrera_id": selected_career_id, # Store ID
                    "carrera": selected_career_name, # Store Name
                    "semestre": semestre
                })
                st.session_state["user"] = request_user
                st.session_state["registro_step"] = 2
                st.rerun()

    elif step == 2:
        st.subheader("Paso 2: Datos del Proyecto DUAL")
        
        # Load Companies
        res_ue = supabase.table("unidades_economicas").select("id, nombre_comercial").execute()
        ues = res_ue.data if res_ue.data else []
        ue_options = {ue["nombre_comercial"]: ue["id"] for ue in ues}
        
        col_ue_sel, col_dummy = st.columns(2)
        with col_ue_sel:
             selected_ue_name = st.selectbox("Seleccionar Unidad Económica", list(ue_options.keys()) if ues else ["No disponible"])
             ue_id = ue_options.get(selected_ue_name)

        mentors = []
        if ue_id:
            res_mentors = supabase.table("mentores_ue").select("id, nombre_completo").eq("ue_id", ue_id).execute()
            mentors = res_mentors.data
        
        mentor_options = {m["nombre_completo"]: m["id"] for m in mentors}

        col_p1, col_p2 = st.columns(2)
        with col_p1:
                selected_mentor_name = st.selectbox("Mentor UE (Industrial)", list(mentor_options.keys()) if mentors else ["No hay mentores registrados"])
                mentor_id = mentor_options.get(selected_mentor_name)
                
                nombre_proyecto = st.text_input("Nombre del Proyecto", value=st.session_state.get("project_data", {}).get("nombre_proyecto", ""))
        
        with col_p2:
                fecha_inicio = st.date_input("Fecha Inicio Convenio", value=st.session_state.get("project_data", {}).get("fecha_inicio", date.today()))
                fecha_fin = st.date_input("Fecha Fin Convenio", value=st.session_state.get("project_data", {}).get("fecha_fin", date.today()))
        
        # Validation Display
        if fecha_inicio and fecha_fin:
             if fecha_inicio == fecha_fin:
                  st.error("⚠️ La fecha de inicio y fin no pueden ser iguales.")
             elif fecha_inicio > fecha_fin:
                  st.error("⚠️ La fecha de inicio no puede ser posterior a la fecha fin.")
             else:
                  delta = fecha_fin - fecha_inicio
                  days = delta.days
                  if 360 <= days <= 370:
                       st.success(f"Duración: {days} días (Aprox. 1 Año) ✅")
                  else:
                       st.warning(f"⚠️ **Atención:** La duración del convenio es de {days} días. (No es 1 año exacto).")

        descripcion_proyecto = st.text_area("Descripción del Proyecto", value=st.session_state.get("project_data", {}).get("descripcion_proyecto", ""))

        c_nav1, c_nav2 = st.columns([1,1])
        if c_nav1.button("< Anterior", key="prev2"):
                st.session_state["registro_step"] = 1
                st.rerun()

        if c_nav2.button("Siguiente >", key="next2"):
                if not nombre_proyecto or not ue_id or not mentor_id:
                    st.error("Todos los campos del proyecto son obligatorios (Empresa, Mentor, Nombre Proyecto).")
                elif fecha_inicio == fecha_fin:
                    st.error("Las fechas no pueden ser iguales.")
                elif fecha_inicio > fecha_fin:
                    st.error("La fecha de inicio no puede ser posterior a la fecha fin.")
                else:
                    st.session_state["project_data"] = {
                        "ue_id": ue_id,
                        "mentor_ue_id": mentor_id,
                        "nombre_proyecto": nombre_proyecto,
                        "descripcion_proyecto": descripcion_proyecto,
                        "fecha_inicio": fecha_inicio,
                        "fecha_fin": fecha_fin,
                        "ue_name": selected_ue_name,
                        "mentor_ue_name": selected_mentor_name
                    }
                    st.session_state["registro_step"] = 3
                    st.rerun()

    elif step == 3:
        st.subheader("Paso 3: Registro de Asignaturas")
        
        if "subjects_data" not in st.session_state:
            st.session_state["subjects_data"] = []

        user = st.session_state.get("user", {})

        # Get Context
        selected_career_id = st.session_state.get("selected_career_id", None)
            
        # Fetch Subjects Filtered
        c_filter1, c_filter2 = st.columns(2)
        with c_filter1:
            st.write(f"**Carrera:** {st.session_state.get('selected_career', 'Sistemas')}")
        with c_filter2:
            # Filter by Semester
            sem_options = ["Todos", "6", "7", "8", "9"]
            current_sem = user.get("semestre", "6")
            # Default to student's semester if valid, else 'Todos'
            default_index = sem_options.index(current_sem) if current_sem in sem_options else 0
            
            selected_sem_filter = st.selectbox("Filtrar Materias por Semestre", sem_options, index=default_index)

        query = supabase.table("asignaturas").select("id, nombre, clave_asignatura, semestre")
        if selected_career_id:
             query = query.eq("carrera_id", selected_career_id)
        
        if selected_sem_filter != "Todos":
            query = query.eq("semestre", selected_sem_filter)

        res_subjects = query.execute()
        subjects = res_subjects.data if res_subjects.data else []
        subject_options = {f"{s['clave_asignatura']} - {s['nombre']} (Sem {s['semestre']})": s["id"] for s in subjects}

        st.markdown("##### Agregar Asignatura")
        
        c1, c2 = st.columns(2)
        with c1:
            sel_subj_name = st.selectbox("Asignatura", list(subject_options.keys()) if subjects else ["No hay asignaturas en este semestre"])
            subject_id = subject_options.get(sel_subj_name)
            
            grupo = st.text_input("Grupo (Ej. 8101)")
            
        with c2:
            filtered_teachers = []
            if subject_id:
                res_rels = supabase.table("rel_maestros_asignaturas").select("maestro_id").eq("asignatura_id", subject_id).execute()
                teacher_ids = [r["maestro_id"] for r in res_rels.data] if res_rels.data else []
                
                if teacher_ids:
                    res_teachers = supabase.table("maestros").select("id, clave_maestro, nombre_completo").in_("id", teacher_ids).execute()
                    filtered_teachers = res_teachers.data if res_teachers.data else []
            
            if filtered_teachers:
                # User request: Clean name (remove parenthesis content like '(Mentor ...)')
                cleaned_options = {}
                for t in filtered_teachers:
                    raw_name = t['nombre_completo']
                    clean_name = re.sub(r'\s*\([^)]*\)', '', raw_name).strip()
                    display_str = f"{t['clave_maestro']} - {clean_name}"
                    cleaned_options[display_str] = t["id"]
                
                teacher_options = cleaned_options
            else:
                 teacher_options = {}

            sel_teacher_name = st.selectbox(
                "Maestro (Docente)", 
                list(teacher_options.keys()) if teacher_options else ["No hay maestros asignados a esta materia"]
            )
            
            st.write("Parciales a Cursar:")
            col_chk1, col_chk2, col_chk3 = st.columns(3)
            with col_chk1: p1 = st.checkbox("Parcial 1", value=True)
            with col_chk2: p2 = st.checkbox("Parcial 2", value=True)
            with col_chk3: p3 = st.checkbox("Parcial 3", value=True)

        if st.button("Agregar Materia"):
             if not grupo:
                  st.error("Ingrese el grupo.")
             elif not sel_teacher_name or sel_teacher_name == "No hay maestros asignados a esta materia":
                  st.error("Seleccione un maestro válido.")
             else:
                  st.session_state["subjects_data"].append({
                      "asignatura_id": subject_id,
                      "maestro_id": teacher_options[sel_teacher_name],
                      "grupo": grupo,
                      "asignatura_name": sel_subj_name, 
                      "maestro_name": sel_teacher_name,
                      "p1": p1, "p2": p2, "p3": p3
                  })
                  st.success("Materia agregada.")

        # Show Added Table
        if st.session_state["subjects_data"]:
            st.markdown("##### Materias Inscritas")
            for idx, item in enumerate(st.session_state["subjects_data"]):
                with st.container():
                     cols = st.columns([3, 3, 1, 3])
                     cols[0].write(f"**{item['asignatura_name']}**")
                     cols[1].write(f"{item['maestro_name']}")
                     cols[2].write(f"Gpo: {item['grupo']}")
                     partials = []
                     if item['p1']: partials.append("P1")
                     if item['p2']: partials.append("P2")
                     if item['p3']: partials.append("P3")
                     cols[3].write(f"Eval: {', '.join(partials)}")
            
            if st.button("Limpiar Lista de Materias"):
                st.session_state["subjects_data"] = []
                st.rerun()

        col_nav1, col_nav2 = st.columns([1, 1])
        if col_nav1.button("< Anterior", key="prev3"):
             st.session_state["registro_step"] = 2
             st.rerun()
        if col_nav2.button("Finalizar y Registrar >", key="next3"):
             if not st.session_state["subjects_data"]:
                  st.error("Debe inscribir al menos una materia.")
             else:
                  st.session_state["registro_step"] = 4
                  st.rerun()

    elif step == 4:
        st.subheader("Resumen y Confirmación")
        
        user = st.session_state.get("user", {})
        proj = st.session_state.get("project_data", {})
        subjs = st.session_state.get("subjects_data", [])
        
        st.info("Por favor revise cuidadosamente la información. Si todo es correcto, haga clic en 'Confirmar y Enviar Registro'.")
        
        with st.expander("Datos Personales y Académicos", expanded=True):
             c1, c2, c3 = st.columns(3)
             c1.markdown(f"**Nombre:** {user.get('nombre')} {user.get('ap_paterno')} {user.get('ap_materno')}")
             c1.markdown(f"**Matrícula:** {user.get('matricula')}")
             c1.markdown(f"**Género:** {user.get('genero')}")
             
             c2.markdown(f"**CURP:** {user.get('curp')}")
             c2.markdown(f"**NSS:** {user.get('nss')}")
             c2.markdown(f"**Estado Civil:** {user.get('estado_civil')}")
             
             c3.markdown(f"**Email Inst:** {user.get('email_institucional')}")
             c3.markdown(f"**Email Pers:** {user.get('email_personal')}")
             c3.markdown(f"**Teléfono:** {user.get('telefono')}")
             
             st.markdown("---")
             c4, c5 = st.columns(2)
             c4.markdown(f"**Carrera:** {user.get('carrera')}")
             c5.markdown(f"**Semestre:** {user.get('semestre')}")
             c5.markdown(f"**Fecha Nac:** {user.get('fecha_nacimiento')}")
             
        with st.expander("Datos del Proyecto Dual", expanded=True):
             st.markdown(f"**Empresa:** {proj.get('ue_name')}")
             st.markdown(f"**Proyecto:** {proj.get('nombre_proyecto')}")
             st.markdown(f"**Mentor:** {proj.get('mentor_ue_name')}")
             st.markdown(f"**Vigencia:** {proj.get('fecha_inicio')} al {proj.get('fecha_fin')}")
             st.markdown(f"**Descripción:** {proj.get('descripcion_proyecto')}")
             
        st.markdown("### Carga Académica")
        st.markdown("""
        | Asignatura | Maestro | Grupo |
        | :--- | :--- | :--- |
        """)
        for s in subjs:
             st.markdown(f"| {s['asignatura_name']} | {s['maestro_name']} | {s['grupo']} |")

        if st.button("Confirmar y Enviar Registro"):
            with st.spinner("Guardando registro en sistema..."):
                # Attempt transaction
                success, msg = create_student_transaction(user, proj, subjs)
                if success:
                    st.balloons()
                    st.success("¡Registro completado exitosamente y datos actualizados!")
                    
                    # Email sending
                    try:
                        from src.utils.email_sender import send_confirmation_email
                        
                        email_data = {
                            "nombre": f"{user.get('nombre')} {user.get('ap_paterno')}",
                            "matricula": user.get("matricula"),
                            "carrera": user.get("carrera"),
                            "proyecto": proj.get("nombre_proyecto"),
                            "ue": proj.get("ue_name"),
                            "fecha_inicio": proj.get("fecha_inicio")
                        }
                        
                        sent = send_confirmation_email(user.get("email_personal"), email_data)
                        if sent:
                            st.toast("Correo de confirmación enviado.", icon="📧")
                    except Exception as e:
                         st.error(f"No se pudo enviar el correo: {e}")

                    st.session_state["registro_complete"] = True
                    # Update User Context to "Registered Student"
                    st.session_state["role"] = "student"
                    # Update user data with ID and new details
                    st.session_state["user"] = msg
                    st.session_state["user"]["estatus"] = "Registrado"
                    
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Error al guardar: {msg}")
        
        if st.button("< Corregir"):
             st.session_state["registro_step"] = 3
             st.rerun()
