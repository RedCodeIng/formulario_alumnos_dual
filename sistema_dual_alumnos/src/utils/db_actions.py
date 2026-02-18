import streamlit as st
from datetime import date
from src.db_connection import get_supabase_client

def get_active_period_id():
    """Fetches the ID of the currently active period."""
    supabase = get_supabase_client()
    response = supabase.table("periodos").select("id").eq("activo", True).execute()
    if response.data:
        return response.data[0]["id"]
    return None

def create_student_transaction(student_data, project_data, subjects_data):
    """
    Executes the registration transaction:
    1. Create Student
    2. Create Dual Project (assigned to active period)
    3. Register Subjects
    """
    supabase = get_supabase_client()
    period_id = get_active_period_id()
    
    if not period_id:
        return False, "No hay periodo activo configurado."

    try:
        # 1. Register Student
        # Check if exists first to avoid duplicate key error if reusing matricula for retries
        # For MVP we assume new student or update? 
        # "upsert" is better for handling retries or existing pre-registered students
        
        # Prepare student record
        student_record = {
            "matricula": student_data["matricula"],
            "curp": student_data["curp"],
            "nombre": student_data["nombre"],
            "ap_paterno": student_data["ap_paterno"],
            "ap_materno": student_data["ap_materno"],
            "nss": student_data.get("nss"),
            "email_personal": student_data.get("email_personal"),
            "email_institucional": student_data.get("email_institucional"),
            "telefono": student_data.get("telefono"),
            "genero": student_data.get("genero"),
            "estado_civil": student_data.get("estado_civil"),
            "fecha_nacimiento": student_data["fecha_nacimiento"].isoformat() if hasattr(student_data["fecha_nacimiento"], 'isoformat') else student_data["fecha_nacimiento"],
            "carrera_id": student_data.get("carrera_id"), # NEW
            "estatus": "Registrado"
        }
        
        # Using Upsert to handle potential pre-filled data updates
        res_student = supabase.table("alumnos").upsert(student_record, on_conflict="matricula").execute()
        
        if not res_student.data:
             return False, "Error al guardar datos del alumno."
        
        student_id = res_student.data[0]["id"]

        # 2. Register Project
        f_inicio = project_data["fecha_inicio"]
        f_fin = project_data["fecha_fin"]
        
        project_record = {
            "alumno_id": student_id,
            "periodo_id": period_id,
            "ue_id": project_data["ue_id"],
            "mentor_ue_id": project_data["mentor_ue_id"],
            "nombre_proyecto": project_data["nombre_proyecto"],
            "descripcion_proyecto": project_data.get("descripcion_proyecto"),
            "fecha_inicio_convenio": f_inicio.isoformat() if hasattr(f_inicio, 'isoformat') else f_inicio,
            "fecha_fin_convenio": f_fin.isoformat() if hasattr(f_fin, 'isoformat') else f_fin
        }
        
        # Upsert to handle updates/corrections
        supabase.table("proyectos_dual").upsert(project_record, on_conflict="alumno_id, periodo_id").execute()

        # 3. Register Subjects
        subjects_records = []
        for subject in subjects_data:
            subjects_records.append({
                "alumno_id": student_id,
                "periodo_id": period_id,
                "asignatura_id": subject["asignatura_id"],
                "maestro_id": subject["maestro_id"], # Evaluator
                "grupo": subject.get("grupo"),
                "parcial_1": subject.get("p1", True),
                "parcial_2": subject.get("p2", True),
                "parcial_3": subject.get("p3", True)
            })
            
        if subjects_records:
            supabase.table("inscripciones_asignaturas").insert(subjects_records).execute()
        
        student_record["id"] = student_id
        return True, student_record

    except Exception as e:
        return False, str(e)
