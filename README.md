
# Proyecto2_BD

Este proyecto forma parte del curso de **Bases de Datos** y tiene como objetivo principal desarrollar y gestionar una base de datos relacional, así como simular operaciones concurrentes sobre la misma.

## 📂 Estructura del Proyecto

El repositorio contiene los siguientes archivos:

- `Fase1Proyecto2_BD.sql`: Script SQL correspondiente a la primera fase del proyecto.
- `Fase2Proyecto2_BD.sql`: Script SQL correspondiente a la segunda fase del proyecto.
- `Simulacion_Concurrencia.py`: Script en Python que simula operaciones concurrentes en la base de datos.
- `Sistema_Concurrencia.py`: Script en Python que permite elegir manualmente las opciones de concurrencia a simular.

## 🛠️ Tecnologías Utilizadas

- **Base de Datos**: [Especificar el gestor de base de datos utilizado, por ejemplo, MySQL, PostgreSQL, SQL Server, etc.]
- **Lenguaje de Programación**: Python (utilizado para la simulación de concurrencia)

## 🚀 Cómo Empezar

Para utilizar este proyecto, sigue los siguientes pasos:

### 1. Configuración de la Base de Datos:

- Ejecuta el script `Fase1Proyecto2_BD.sql` en tu gestor de base de datos para crear la estructura inicial.
- Luego, ejecuta el script `Fase2Proyecto2_BD.sql` para aplicar las modificaciones correspondientes a la segunda fase.

### 2. Simulación de Concurrencia:

- Asegúrate de tener Python instalado en tu sistema.
- Instala las dependencias necesarias para ejecutar los scripts Python (si las hay).
- Verifica en la función de conexión los siguientes datos de configuración:

```python
# Configuración de la base de datos
CONFIG_BD = {
    'dbname': 'Proyecto2',        # Nombre de la base de datos
    'user': 'postgres',           # Usuario de PostgreSQL
    'password': '123456789',      # Contraseña del usuario
    'host': 'localhost',          # Dirección del servidor
    'port': 5432                  # Puerto por defecto de PostgreSQL
}
updated_readme_content = readme_content.strip() + """
```
### ℹ️ Notas Adicionales

- Si ejecutas `python3 Sistema_Concurrencia.py`, podrás **elegir manualmente** las opciones de concurrencia a simular.
- Si ejecutas `python3 Simulacion_Concurrencia.py --todas`, se **ejecutarán automáticamente** todos los niveles de aislamiento (READ COMMITTED, REPEATABLE READ, SERIALIZABLE) con números fijos de hilos, **sin posibilidad de elegir opciones**.



