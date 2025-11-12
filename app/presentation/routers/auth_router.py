# presentation/routers/auth_router.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, List

from application.dto.usuario_dto import RegistroUsuarioDTO, LoginDTO, UsuarioRespuestaDTO, TokenDTO, SaldoUpdateDTO, UsuarioListaDTO
from domain.services.autenticacion_service import AutenticacionService
from domain.exceptions.exceptions import UsuarioYaExisteError, CredencialesInvalidasError, UsuarioNoEncontradoError
from domain.models.usuario import Usuario, RolUsuario
from infrastructure.database.postgresql_repository import PostgresqlUsuarioRepository, PostgresqlConnectionManager, get_connection_manager
from infrastructure.security.password_hasher import PasswordHasher
from infrastructure.security.jwt_handler import JWTHandler

router = APIRouter(tags=["autenticación"])

# Esquema OAuth2 para obtener el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token") 

# --- Dependencias ---

def get_password_hasher():
    return PasswordHasher()

def get_jwt_handler():
    return JWTHandler()

def get_autenticacion_service(
    connection_manager: PostgresqlConnectionManager = Depends(get_connection_manager),
    password_hasher: PasswordHasher = Depends(get_password_hasher)
):
    usuario_repository = PostgresqlUsuarioRepository(connection_manager)
    return AutenticacionService(usuario_repository, password_hasher)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    autenticacion_service: AutenticacionService = Depends(get_autenticacion_service),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> Usuario:
    """
    Dependencia para obtener el usuario actual a partir del token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = jwt_handler.verify_access_token(token)
    if payload is None:
        raise credentials_exception
        
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
        
    try:
        user = autenticacion_service.obtener_usuario_por_nombre(username)
        return user
    except UsuarioNoEncontradoError:
        raise credentials_exception

async def get_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependencia para verificar que el usuario actual es administrador.
    """
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    return current_user

def verify_user_access(target_username: str, current_user: Usuario) -> None:
    """
    Verifica que el usuario tenga acceso a los datos solicitados.
    Solo el propio usuario o un admin pueden acceder.
    """
    if current_user.usuario != target_username and current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso"
        )

class AuthController:
    """Controlador para manejar las operaciones de autenticación."""
    
    def __init__(
        self, 
        autenticacion_service: AutenticacionService,
        jwt_handler: JWTHandler
    ):
        self.autenticacion_service = autenticacion_service
        self.jwt_handler = jwt_handler
        
    def registrar_usuario(self, datos: RegistroUsuarioDTO) -> Dict[str, Any]:
        """Registra un nuevo usuario."""
        try:
            usuario = self.autenticacion_service.registrar_usuario(
                datos.usuario, 
                datos.contraseña, 
                datos.nombre, 
                datos.rol
            )
            return {
                "mensaje": "Usuario registrado exitosamente", 
                "usuario": usuario.usuario,
                "nombre": usuario.nombre,
                "rol": usuario.rol.value
            }
        except UsuarioYaExisteError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
            
    def login_for_access_token(self, datos: LoginDTO) -> TokenDTO:
        """Autentica y retorna un token JWT."""
        try:
            usuario = self.autenticacion_service.autenticar(datos.usuario, datos.contraseña)
            access_token = self.jwt_handler.create_access_token(
                data={"sub": usuario.usuario, "rol": usuario.rol.value}
            )
            return TokenDTO(access_token=access_token)
        except (UsuarioNoEncontradoError, CredencialesInvalidasError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Usuario o contraseña incorrectos"
            )
            
    def obtener_usuario_por_nombre(self, nombre_usuario: str) -> UsuarioRespuestaDTO:
        """Obtiene datos de un usuario por nombre."""
        try:
            usuario = self.autenticacion_service.obtener_usuario_por_nombre(nombre_usuario)
            return UsuarioRespuestaDTO.model_validate(usuario.__dict__)
        except UsuarioNoEncontradoError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
            
    def actualizar_saldo(self, nombre_usuario: str, recarga: float) -> UsuarioRespuestaDTO:
        """Recarga saldo."""
        try:
            usuario = self.autenticacion_service.actualizar_saldo_usuario(nombre_usuario, recarga)
            return UsuarioRespuestaDTO.model_validate(usuario.__dict__)
        except UsuarioNoEncontradoError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
            
    def descargar_saldo(self, nombre_usuario: str, descarga: float) -> UsuarioRespuestaDTO:
        """Descarga saldo."""
        try:
            usuario = self.autenticacion_service.descargar_saldo_usuario(nombre_usuario, descarga)
            return UsuarioRespuestaDTO.model_validate(usuario.__dict__)
        except UsuarioNoEncontradoError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# --- Dependencia del Controlador ---

def get_auth_controller(
    autenticacion_service: AutenticacionService = Depends(get_autenticacion_service),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
):
    return AuthController(autenticacion_service, jwt_handler)

# --- Endpoints Públicos (SIN AUTENTICACIÓN) ---

@router.post("/registrar", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def registrar_usuario_endpoint(
    datos: RegistroUsuarioDTO,
    auth_controller: AuthController = Depends(get_auth_controller)
) -> Dict[str, Any]:
    """
    Endpoint para registrar un nuevo usuario.
    ⚠️ TEMPORAL: Sin autenticación para pruebas
    """
    return auth_controller.registrar_usuario(datos)

@router.get("/usuarios/rol/{rol}", response_model=List[UsuarioListaDTO])
async def listar_usuarios_por_rol_endpoint(
    rol: str,
    autenticacion_service: AutenticacionService = Depends(get_autenticacion_service)
) -> List[UsuarioListaDTO]:
    """
    Endpoint para listar usuarios por rol.
    ⚠️ TEMPORAL: Sin autenticación para pruebas
    """
    try:
        usuarios = autenticacion_service.listar_usuarios_por_rol(rol)
        return [UsuarioListaDTO(
            id=u.id,
            usuario=u.usuario,
            nombre=u.nombre
        ) for u in usuarios]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar usuarios: {str(e)}")

@router.post("/login", response_model=TokenDTO)
async def login_endpoint(
    datos: LoginDTO,
    auth_controller: AuthController = Depends(get_auth_controller)
) -> TokenDTO:
    """Endpoint para iniciar sesión y obtener un token JWT."""
    return auth_controller.login_for_access_token(datos)

@router.post("/token", response_model=TokenDTO, include_in_schema=False)
async def login_for_access_token_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_controller: AuthController = Depends(get_auth_controller)
) -> TokenDTO:
    """Endpoint para login usando form-data (estándar OAuth2)."""
    login_data = LoginDTO(usuario=form_data.username, contraseña=form_data.password)
    return auth_controller.login_for_access_token(login_data)

# --- Endpoints Protegidos (CON AUTENTICACIÓN) ---

@router.get("/me", response_model=UsuarioRespuestaDTO)
async def read_users_me(current_user: Usuario = Depends(get_current_user)):
    """Endpoint para obtener los datos del usuario actualmente autenticado."""
    return UsuarioRespuestaDTO.parse_obj(current_user.__dict__)

@router.get("/usuarios/{usuario}", response_model=UsuarioRespuestaDTO)
async def obtener_usuario_endpoint(
    usuario: str,
    auth_controller: AuthController = Depends(get_auth_controller),
    current_user: Usuario = Depends(get_current_user)
) -> UsuarioRespuestaDTO:
    """
    Endpoint para obtener un usuario por nombre.
    Solo el propio usuario o un admin pueden acceder.
    """
    verify_user_access(usuario, current_user)
    return auth_controller.obtener_usuario_por_nombre(usuario)

@router.post("/usuarios/{usuario}/recarga-saldo", response_model=UsuarioRespuestaDTO)
async def actualizar_saldo_endpoint(
    usuario: str,
    recarga_data: SaldoUpdateDTO,
    auth_controller: AuthController = Depends(get_auth_controller),
    current_user: Usuario = Depends(get_current_user)
) -> UsuarioRespuestaDTO:
    """
    Endpoint para recargar saldo.
    Solo el propio usuario o un admin pueden realizar esta acción.
    """
    verify_user_access(usuario, current_user)
    return auth_controller.actualizar_saldo(usuario, recarga_data.monto)

@router.post("/usuarios/{usuario}/descarga-saldo", response_model=UsuarioRespuestaDTO)
async def descarga_saldo_endpoint(
    usuario: str,
    descarga_data: SaldoUpdateDTO,
    auth_controller: AuthController = Depends(get_auth_controller),
    current_user: Usuario = Depends(get_current_user)
) -> UsuarioRespuestaDTO:
    """
    Endpoint para descargar saldo.
    Solo el propio usuario o un admin pueden realizar esta acción.
    """
    verify_user_access(usuario, current_user)
    return auth_controller.descargar_saldo(usuario, descarga_data.monto)