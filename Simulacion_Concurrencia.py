# Importamos las librerías necesarias para el programa
import threading           # Para crear múltiples hilos (simulación de usuarios simultáneos)
import psycopg2            # Para conectarse a la base de datos PostgreSQL
import time                # Para medir el tiempo de ejecución y pausar entre hilos
import random              # Para generar números aleatorios
from datetime import datetime
import argparse            # Para procesar argumentos de línea de comandos

# Configuración de la base de datos
CONFIG_BD = {
    'dbname': 'Proyecto2',  # Nombre de la base de datos
    'user': 'postgres',            # Usuario de PostgreSQL
    'password': '1999',          # Contraseña del usuario
    'host': 'localhost',           # Dirección del servidor
    'port': 5432                   # Puerto por defecto de PostgreSQL
}

# Función que simula que un usuario intenta reservar un asiento
def reservar_asiento(id_usuario, id_evento, numero_asiento, nivel_aislamiento, resultados):
    tiempo_inicio = time.time()
    exito = False
    error_msg = None
    
    try:
        # Se conecta a la base de datos usando la configuración definida
        conexion = psycopg2.connect(**CONFIG_BD)
        
        # Establece el nivel de aislamiento para controlar cómo se comportan las transacciones
        conexion.set_session(isolation_level=nivel_aislamiento)
        
        # Crea un cursor para ejecutar comandos SQL
        cursor = conexion.cursor()
        
        print(f"[Usuario {id_usuario}] Iniciando reserva del asiento {numero_asiento} para el evento {id_evento}...")
        
        # Inicia manualmente una transacción
        cursor.execute("BEGIN;")
        
        # Consulta el ID del asiento basado en el evento y número de asiento
        cursor.execute(
            "SELECT id_asiento, estado FROM asientos WHERE id_evento = %s AND numero_asiento = %s FOR UPDATE;", 
            (id_evento, numero_asiento)
        )
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"[Usuario {id_usuario}] ❌ El asiento {numero_asiento} no existe para el evento {id_evento}.")
            conexion.rollback()
            error_msg = "Asiento no existe"
        else:
            id_asiento, estado = resultado
            
            # Si ya está reservado, cancela la transacción
            if estado == 'reservado':
                print(f"[Usuario {id_usuario}] ❌ El asiento {numero_asiento} ya está reservado.")
                conexion.rollback()
                error_msg = "Asiento ya reservado"
            else:
                # Si está disponible, lo marca como reservado
                cursor.execute(
                    "UPDATE asientos SET estado = 'reservado' WHERE id_asiento = %s;", 
                    (id_asiento,)
                )
                
                # Inserta el registro de la reserva
                cursor.execute(
                    "INSERT INTO reservas (id_evento, id_asiento, id_usuario, fecha_reserva) VALUES (%s, %s, %s, %s);",
                    (id_evento, id_asiento, id_usuario, datetime.now())
                )
                
                # Confirma la transacción
                conexion.commit()
                print(f"[Usuario {id_usuario}] ✅ ¡Reserva exitosa del asiento {numero_asiento}!")
                exito = True
                
    except Exception as error:
        print(f"[Usuario {id_usuario}] ❌ Error: {error}")
        error_msg = str(error)
        try:
            conexion.rollback()
        except:
            pass
    
    finally:
        try:
            cursor.close()
            conexion.close()
        except:
            pass
        
        tiempo_total = round((time.time() - tiempo_inicio) * 1000, 2)  # Tiempo en milisegundos
        print(f"[Usuario {id_usuario}] Tiempo de procesamiento: {tiempo_total} ms")
        
        # Almacenar resultados
        resultados.append({
            'usuario': id_usuario,
            'exito': exito,
            'error': error_msg,
            'tiempo': tiempo_total
        })

# Función para listar eventos disponibles
def listar_eventos():
    try:
        conexion = psycopg2.connect(**CONFIG_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT id_evento, nombre, fecha FROM eventos ORDER BY id_evento;")
        eventos = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        print("\n=== EVENTOS DISPONIBLES ===")
        for evento in eventos:
            print(f"ID: {evento[0]} | Nombre: {evento[1]} | Fecha: {evento[2]}")
        print("=========================\n")
        return eventos
    except Exception as error:
        print(f"Error al listar eventos: {error}")
        return []

# Menú interactivo para configurar la simulación
def menu_interactivo():
    print("\n🎭 SIMULADOR DE CONCURRENCIA EN SISTEMA DE RESERVAS 🎭")
    print("==================================================")
    
    # Mostrar información de conexión a la BD
    print("\n📊 Configuración de la base de datos:")
    print(f"  Nombre: {CONFIG_BD['dbname']}")
    print(f"  Usuario: {CONFIG_BD['user']}")
    print(f"  Host: {CONFIG_BD['host']}:{CONFIG_BD['port']}")
    print("  Si necesitas cambiar estos datos, edita la variable CONFIG_BD en el código.")
    
    # Prueba de conexión a la BD
    try:
        conexion = psycopg2.connect(**CONFIG_BD)
        conexion.close()
        print("  ✅ Conexión a la base de datos exitosa.")
    except Exception as error:
        print(f"  ❌ No se pudo conectar a la base de datos: {error}")
        print("  Por favor verifica la configuración e intenta nuevamente.")
        return
    
    # Listar eventos disponibles
    eventos = listar_eventos()
    if not eventos:
        print("❌ No se encontraron eventos. Verifica la base de datos.")
        return
    
    # Seleccionar evento
    while True:
        try:
            id_evento = int(input("👉 Ingrese el ID del evento a utilizar: "))
            # Verificar si el evento existe
            if any(evento[0] == id_evento for evento in eventos):
                break
            else:
                print("❌ ID de evento no válido. Intente nuevamente.")
        except ValueError:
            print("❌ Por favor ingrese un número válido.")
    
    # Número de asientos
    while True:
        try:
            num_asientos = int(input("👉 Ingrese el número de asientos a crear para el evento (10-100): "))
            if 10 <= num_asientos <= 100:
                break
            else:
                print("❌ El número de asientos debe estar entre 10 y 100.")
        except ValueError:
            print("❌ Por favor ingrese un número válido.")
    
    # Preparar los asientos para el evento
    if not preparar_asientos(id_evento, num_asientos):
        print("❌ No se pudieron preparar los asientos. Abortando simulación.")
        return
    
    # Número de usuarios (hilos) para la simulación
    while True:
        try:
            num_usuarios = int(input("👉 Ingrese el número de usuarios concurrentes a simular (1-50): "))
            if 1 <= num_usuarios <= 50:
                break
            else:
                print("❌ El número de usuarios debe estar entre 1 y 50.")
        except ValueError:
            print("❌ Por favor ingrese un número válido.")
    
    # Nivel de aislamiento
    print("\n👉 Seleccione el nivel de aislamiento:")
    print("  1. READ COMMITTED (menor protección, mayor rendimiento)")
    print("  2. REPEATABLE READ (protección media)")
    print("  3. SERIALIZABLE (mayor protección, menor rendimiento)")
    
    while True:
        try:
            opcion = int(input("Opción (1-3): "))
            if 1 <= opcion <= 3:
                niveles = ["READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"]
                nivel_aislamiento = niveles[opcion-1]
                break
            else:
                print("❌ Opción no válida. Intente nuevamente.")
        except ValueError:
            print("❌ Por favor ingrese un número válido.")
    
    # Porcentaje de conflicto
    while True:
        try:
            porcentaje_conflicto = int(input("👉 Ingrese el porcentaje de conflicto deseado (0-100): "))
            if 0 <= porcentaje_conflicto <= 100:
                break
            else:
                print("❌ El porcentaje debe estar entre 0 y 100.")
        except ValueError:
            print("❌ Por favor ingrese un número válido.")
    
    # Resumen de la configuración
    print("\n✅ CONFIGURACIÓN DE LA SIMULACIÓN:")
    print(f"  • Evento: ID {id_evento}")
    print(f"  • Asientos disponibles: {num_asientos}")
    print(f"  • Usuarios concurrentes: {num_usuarios}")
    print(f"  • Nivel de aislamiento: {nivel_aislamiento}")
    print(f"  • Porcentaje de conflicto: {porcentaje_conflicto}%")
    
    confirmacion = input("\n¿Desea iniciar la simulación con esta configuración? (s/n): ").lower()
    if confirmacion == 's':
        print("\n🚀 Iniciando simulación...\n")
        ejecutar_simulacion(
            numero_usuarios=num_usuarios,
            aislamiento=nivel_aislamiento,
            id_evento=id_evento,
            porcentaje_conflicto=porcentaje_conflicto
        )
    else:
        print("\n❌ Simulación cancelada.")

# Punto de entrada del programa
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simulación de reservas concurrentes')
    parser.add_argument('--usuarios', type=int, help='Número de usuarios concurrentes', default=0)
    parser.add_argument('--aislamiento', choices=['READ COMMITTED', 'REPEATABLE READ', 'SERIALIZABLE'], 
                        help='Nivel de aislamiento', default='READ COMMITTED')
    parser.add_argument('--evento', type=int, help='ID del evento para reservar', default=0)
    parser.add_argument('--asientos', type=int, help='Número de asientos a crear para el evento', default=0)
    parser.add_argument('--conflicto', type=int, help='Porcentaje de intentos conflictivos (0-100)', default=30)
    parser.add_argument('--todas', action='store_true', help='Ejecutar todas las pruebas requeridas')
    parser.add_argument('--interactivo', action='store_true', help='Ejecutar en modo interactivo (menú)')
    
    args = parser.parse_args()
    
    # Si se especifica el modo interactivo o no se proporciona ningún parámetro, mostrar el menú
    if args.interactivo or (args.usuarios == 0 and args.evento == 0 and not args.todas):
        menu_interactivo()
    # Si se especifica ejecutar todas las pruebas
    elif args.todas:
        # Si no se especificó un evento, usar el evento 1 por defecto
        id_evento = args.evento if args.evento > 0 else 1
        
        # Si se especificó un número de asientos, preparar los asientos
        if args.asientos > 0:
            preparar_asientos(id_evento, args.asientos)
            
        ejecutar_todas_pruebas(id_evento)
    # Si se especifican parámetros para una simulación individual
    else:
        # Si no se especificó un evento, usar el evento 1 por defecto
        id_evento = args.evento if args.evento > 0 else 1
        
        # Si se especificó un número de asientos, preparar los asientos
        if args.asientos > 0:
            preparar_asientos(id_evento, args.asientos)
            
        ejecutar_simulacion(
            numero_usuarios=args.usuarios if args.usuarios > 0 else 5,
            aislamiento=args.aislamiento,
            id_evento=id_evento,
            porcentaje_conflicto=args.conflicto
        )