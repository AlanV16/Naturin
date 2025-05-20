from django.db import models
from django.contrib.auth.models import User
from apps.accounts.models import User as CustomUser
from django.urls import reverse

ESTADO_CONSERVACION = (
    ('LC', 'Preocupación menor'),
    ('NT', 'Casi amenazada'),
    ('VU', 'Vulnerable'),
    ('EN', 'En peligro'),
    ('CR', 'En peligro crítico'),
)

# MODELOS BÁSICOS

class Categoria(models.Model):
    categoria = models.CharField(max_length=20)
    def __str__(self):
        return self.categoria

class Distrito(models.Model):
    distrito = models.CharField(max_length=20)
    def __str__(self):
        return self.distrito

class EpocaFloracion(models.Model):
    epoca_floracion = models.CharField(max_length=20)
    def __str__(self):
        return self.epoca_floracion

class EstadoDeConservacion(models.Model):
    codigo = models.CharField(max_length=2, choices=ESTADO_CONSERVACION)
    descripcion = models.CharField(max_length=50)
    def __str__(self):
        return self.get_codigo_display()

class GradoDeNivelEducativo(models.Model):
    grado = models.CharField(max_length=20)
    def __str__(self):
        return self.grado

class Habitat(models.Model):
    habitat = models.CharField(max_length=50)
    def __str__(self):
        return self.habitat

class Locacion(models.Model):
    locacion = models.CharField(max_length=200)
    def __str__(self):
        return self.locacion

class ModoDeReproduccion(models.Model):
    modo_reproduccion = models.CharField(max_length=50)
    def __str__(self):
        return self.modo_reproduccion

class NivelEducativo(models.Model):
    nivel = models.CharField(max_length=20)
    def __str__(self):
        return self.nivel

class PeligroHumano(models.Model):
    nivel_peligro = models.CharField(max_length=50)
    def __str__(self):
        return self.nivel_peligro

class TipoActividad(models.Model):
    tipo_actividad = models.CharField(max_length=100)
    def __str__(self):
        return self.tipo_actividad

class TipoAlimentacion(models.Model):
    alimentacion = models.CharField(max_length=20)
    def __str__(self):
        return self.alimentacion

class TipoAnimal(models.Model):
    tipo_animal = models.CharField(max_length=50)
    def __str__(self):
        return self.tipo_animal

class TipoCalle(models.Model):
    tipo_calle = models.CharField(max_length=50)
    def __str__(self):
        return self.tipo_calle

class TipoEspecie(models.Model):
    nombre = models.CharField(max_length=50)  # Cambiado de 'especie' a 'nombre'
    def __str__(self):
        return self.nombre

class TipoEstadoNivelEducativo(models.Model):
    estado = models.CharField(max_length=20)
    def __str__(self):
        return self.estado

class TipoFlor(models.Model):
    tipo_flor = models.CharField(max_length=50)
    def __str__(self):
        return self.tipo_flor

class TipoInstitucion(models.Model):
    tipo_institucion = models.CharField(max_length=50)
    def __str__(self):
        return self.tipo_institucion

class TipoJuego(models.Model):
    tipo_juego = models.CharField(max_length=50)
    def __str__(self):
        return self.tipo_juego

class TipoMultimedia(models.Model):
    tipo_multimedia = models.CharField(max_length=100)
    def __str__(self):
        return self.tipo_multimedia

class TipoPlanta(models.Model):
    tipo = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200)
    def __str__(self):
        return self.tipo

class TipoReproduccion(models.Model):
    reproduccion = models.CharField(max_length=20)
    def __str__(self):
        return self.reproduccion

class TipoSuelo(models.Model):
    suelo = models.CharField(max_length=10)
    def __str__(self):
        return self.suelo

class UsosAlimenticios(models.Model):
    usos_alimenticios = models.CharField(max_length=10)
    def __str__(self):
        return self.usos_alimenticios

class UsosMedicinales(models.Model):
    usos_medicinales = models.CharField(max_length=10)
    def __str__(self):
        return self.usos_medicinales

# MODELOS PRINCIPALES

class Rol(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.nombre_rol

class Usuario(models.Model):
    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    nivel_educativo = models.ForeignKey(NivelEducativo, on_delete=models.SET_NULL, null=True, blank=True)
    grado_nivel_educativo = models.ForeignKey(GradoDeNivelEducativo, on_delete=models.SET_NULL, null=True, blank=True)
    estado_nivel_educativo = models.ForeignKey(TipoEstadoNivelEducativo, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"

class Usos(models.Model):
    usos_alimenticios = models.ForeignKey(UsosAlimenticios, on_delete=models.SET_NULL, null=True, blank=True)
    usos_medicinales = models.ForeignKey(UsosMedicinales, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    def __str__(self):
        return self.descripcion or "Sin descripción"

class Floracion(models.Model):
    epoca_floracion = models.ForeignKey(EpocaFloracion, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_flor = models.ForeignKey(TipoFlor, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    def __str__(self):
        return f"{self.epoca_floracion} - {self.tipo_flor}" if self.epoca_floracion and self.tipo_flor else "Floracion sin detalles"

class Institucion(models.Model):
    nombre_institucion = models.CharField(max_length=100)
    distrito = models.ForeignKey(Distrito, on_delete=models.CASCADE)
    calle = models.CharField(max_length=200)
    numero_calle = models.CharField(max_length=10)
    tipo_calle = models.ForeignKey(TipoCalle, on_delete=models.CASCADE)
    tipo_institucion = models.ForeignKey(TipoInstitucion, on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre_institucion

class Especie(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    tipo_especie = models.ForeignKey(TipoEspecie, on_delete=models.CASCADE, related_name='especies')
    nombre_comun = models.CharField(max_length=100)
    nombre_cientifico = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=500)
    habitat = models.ForeignKey(Habitat, on_delete=models.CASCADE)
    locacion = models.ForeignKey(Locacion, on_delete=models.CASCADE)
    tipo_reproduccion = models.ForeignKey(TipoReproduccion, on_delete=models.CASCADE)
    estado_conservacion = models.ForeignKey(EstadoDeConservacion, on_delete=models.CASCADE)
    peligro = models.ForeignKey(PeligroHumano, on_delete=models.CASCADE)
    tipo_multimedia = models.ForeignKey(TipoMultimedia, on_delete=models.CASCADE)
    archivo_multimedia = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.nombre_comun} ({self.nombre_cientifico})"

class Fauna(models.Model):
    especie = models.OneToOneField(Especie, on_delete=models.CASCADE, primary_key=True)
    tipo_animal = models.ForeignKey(TipoAnimal, on_delete=models.CASCADE)
    tipo_alimentacion = models.ForeignKey(TipoAlimentacion, on_delete=models.CASCADE)
    modo_reproduccion = models.ForeignKey(ModoDeReproduccion, on_delete=models.SET_NULL, null=True, blank=True)
    tiempo_gestacion = models.CharField(max_length=50, null=True, blank=True)
    numero_crias = models.CharField(max_length=50, null=True, blank=True)
    tamaño = models.CharField(max_length=10)
    peso = models.CharField(max_length=10, null=True, blank=True)
    def __str__(self):
        return self.especie.nombre_comun

class Flora(models.Model):
    especie = models.OneToOneField(Especie, on_delete=models.CASCADE, primary_key=True)
    tipo_planta = models.ForeignKey(TipoPlanta, on_delete=models.CASCADE)
    altura_maxima = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    floracion = models.ForeignKey(Floracion, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_suelo = models.ForeignKey(TipoSuelo, on_delete=models.CASCADE)
    usos = models.ForeignKey(Usos, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.especie.nombre_comun

class Ficha(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    especie = models.ForeignKey(Especie, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_multimedia = models.ForeignKey(TipoMultimedia, on_delete=models.CASCADE)
    archivo_url = models.CharField(max_length=255)
    nivel_educativo = models.ForeignKey(NivelEducativo, on_delete=models.CASCADE)
    grado_educativo = models.ForeignKey(GradoDeNivelEducativo, on_delete=models.CASCADE)
    def __str__(self):
        return self.titulo

class Aula(models.Model):
    nombre_aula = models.CharField(max_length=100)
    codigo_aula = models.CharField(max_length=20, unique=True)
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE)
    docente = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.nombre_aula

class AulaEstudiante(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    denominacion_aula = models.CharField(max_length=50)
    class Meta:
        unique_together = ['aula', 'estudiante']
    def __str__(self):
        return f"{self.estudiante} - {self.aula}"

class Actividad(models.Model):
    titulo = models.CharField(max_length=100)
    instrucciones = models.TextField()
    tipo_actividad = models.ForeignKey(TipoActividad, on_delete=models.CASCADE)
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    def __str__(self):
        return self.titulo

class Comentario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, null=True, blank=True)
    comentario = models.CharField(max_length=200, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Comentario de {self.usuario} - {self.fecha}"

class Avistamiento(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    especie = models.ForeignKey(Especie, on_delete=models.CASCADE)
    fecha_avistamiento = models.DateField()
    ubicacion = models.CharField(max_length=150)
    comentario = models.CharField(max_length=200)
    def __str__(self):
        return f"{self.especie} avistado por {self.usuario} en {self.fecha_avistamiento}"

class Juego(models.Model):
    nombre_juego = models.CharField(max_length=100)
    tipo_juego = models.ForeignKey(TipoJuego, on_delete=models.CASCADE)
    instrucciones = models.CharField(max_length=500)
    descripcion = models.CharField(max_length=50)
    nivel_dificultad = models.IntegerField()
    def __str__(self):
        return self.nombre_juego

class JuegoUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE)
    puntaje = models.IntegerField(null=True, blank=True)
    fecha_jugada = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['usuario', 'juego', 'fecha_jugada']
    def __str__(self):
        return f"{self.usuario} - {self.juego} - {self.puntaje}"

class Progreso(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    puntuacion = models.IntegerField(null=True, blank=True)
    completado = models.BooleanField(default=False)
    def __str__(self):
        return f"Progreso de {self.usuario} en {self.actividad}"

class RecompensaUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE) 
    fecha_obtenida = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['usuario', 'juego']
    def __str__(self):
        return f"Recompensa para {self.usuario} en {self.juego}"

# Modelo dummy para evitar errores con Assignment.resources
class EducationalResource(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    archivo = models.FileField(upload_to='recursos/', blank=True, null=True)
    def __str__(self):
        return self.titulo