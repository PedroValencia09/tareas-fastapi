# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, schemas, auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRUD FastAPI con JWT y Neon DB", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS DE AUTENTICACIÓN ---

@app.post("/registro", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    existe = db.query(models.Usuario).filter(models.Usuario.username == usuario.username).first()
    if existe:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
    
    nuevo_usuario = models.Usuario(
        username=usuario.username,
        hashed_password=auth.hashear_password(usuario.password)
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.username == form_data.username).first()
    if not usuario or not auth.verificar_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.crear_access_token(data={"sub": usuario.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ENDPOINTS DE TAREAS (PROTEGIDOS CON JWT) ---

@app.post("/tareas/", response_model=schemas.TareaResponse, status_code=status.HTTP_201_CREATED)
def crear_tarea(
    tarea: schemas.TareaCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.obtener_usuario_actual)
):
    nueva_tarea = models.Tarea(
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        completada=tarea.completada,
        owner_id=current_user.id
    )
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    return nueva_tarea

@app.get("/tareas/", response_model=list[schemas.TareaResponse])
def obtener_tareas(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.obtener_usuario_actual)
):
    return db.query(models.Tarea).filter(models.Tarea.owner_id == current_user.id).offset(skip).limit(limit).all()

@app.get("/tareas/{tarea_id}", response_model=schemas.TareaResponse)
def obtener_tarea(
    tarea_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.obtener_usuario_actual)
):
    tarea = db.query(models.Tarea).filter(
        models.Tarea.id == tarea_id,
        models.Tarea.owner_id == current_user.id
    ).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea

@app.put("/tareas/{tarea_id}", response_model=schemas.TareaResponse)
def actualizar_tarea(
    tarea_id: int,
    tarea_actualizada: schemas.TareaUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.obtener_usuario_actual)
):
    tarea_query = db.query(models.Tarea).filter(
        models.Tarea.id == tarea_id,
        models.Tarea.owner_id == current_user.id
    )
    tarea = tarea_query.first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    datos_actualizacion = tarea_actualizada.model_dump(exclude_unset=True)
    tarea_query.update(datos_actualizacion, synchronize_session=False)
    db.commit()
    db.refresh(tarea)
    return tarea

@app.delete("/tareas/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_tarea(
    tarea_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(auth.obtener_usuario_actual)
):
    tarea = db.query(models.Tarea).filter(
        models.Tarea.id == tarea_id,
        models.Tarea.owner_id == current_user.id
    ).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    db.delete(tarea)
    db.commit()
    return None