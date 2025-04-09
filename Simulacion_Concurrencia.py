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
    'password': '123456789',          # Contraseña del usuario
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

# Diccionario que asocia nombres de niveles de aislamiento con sus valores
niveles_aislamiento = {
    'READ COMMITTED': psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED,
    'REPEATABLE READ': psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ, 
    'SERIALIZABLE': psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
}

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

# Función para preparar asientos para un evento
def preparar_asientos(id_evento, num_asientos):
    try:
        conexion = psycopg2.connect(**CONFIG_BD)
        cursor = conexion.cursor()
        
        # Verificar si el evento existe
        cursor.execute("SELECT nombre FROM eventos WHERE id_evento = %s;", (id_evento,))
        evento = cursor.fetchone()
        
        if not evento:
            print(f"❌ El evento con ID {id_evento} no existe.")
            cursor.close()
            conexion.close()
            return False
        
        # Eliminar asientos anteriores para este evento
        cursor.execute("DELETE FROM reservas WHERE id_evento = %s;", (id_evento,))
        cursor.execute("DELETE FROM asientos WHERE id_evento = %s;", (id_evento,))
        
        # Crear nuevos asientos
        print(f"🔄 Creando {num_asientos} asientos para el evento {id_evento}: {evento[0]}")
        
        # Usar generate_series para inserción masiva
        cursor.execute(
            "INSERT INTO asientos (id_evento, numero_asiento, estado) "
            "SELECT %s, generate_series(1, %s), 'disponible';", 
            (id_evento, num_asientos)
        )
        
        conexion.commit()
        print(f"✅ Se han creado {num_asientos} asientos disponibles para el evento.")
        
        cursor.close()
        conexion.close()
        return True
        
    except Exception as error:
        print(f"Error al preparar asientos: {error}")
        try:
            conexion.rollback()
            conexion.close()
        except:
            pass
        return False

# Función que ejecuta la simulación completa
def ejecutar_simulacion(numero_usuarios, aislamiento, id_evento, porcentaje_conflicto=30):
    print(f"\n=== Simulación con {numero_usuarios} usuarios / Aislamiento: {aislamiento} / Evento: {id_evento} ===")
    
    # Lista para almacenar resultados
    resultados = []
    hilos = []
    
    # Obtener todos los asientos disponibles para el evento
    try:
        conexion = psycopg2.connect(**CONFIG_BD)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT numero_asiento FROM asientos WHERE id_evento = %s AND estado = 'disponible';", 
            (id_evento,)
        )
        asientos_disponibles = [row[0] for row in cursor.fetchall()]
        
        # Obtener nombre del evento
        cursor.execute("SELECT nombre FROM eventos WHERE id_evento = %s;", (id_evento,))
        nombre_evento = cursor.fetchone()[0] if cursor.rowcount > 0 else f"Evento {id_evento}"
        
        cursor.close()
        conexion.close()
        
        print(f"📊 Evento: {nombre_evento}")
        print(f"📊 Asientos disponibles: {len(asientos_disponibles)}")
        
        if len(asientos_disponibles) < numero_usuarios:
            print(f"⚠️ Advertencia: Solo hay {len(asientos_disponibles)} asientos disponibles para {numero_usuarios} usuarios.")
        
        # Asegurar que tenemos suficientes asientos para los usuarios
        if not asientos_disponibles:
            print("❌ No hay asientos disponibles para este evento.")
            return {
                'usuarios': numero_usuarios,
                'nivel_aislamiento': aislamiento,
                'reservas_exitosas': 0,
                'reservas_fallidas': numero_usuarios,
                'tiempo_promedio': 0
            }
            
    except Exception as error:
        print(f"Error al obtener asientos disponibles: {error}")
        return None
    
    tiempo_inicio_global = time.time()
    
    # Crea un hilo por cada usuario simulado
    for i in range(numero_usuarios):
        id_usuario = random.randint(1, 10)  # ID aleatorio entre 1 y 10
        
        # Elegir un asiento aleatorio de los disponibles o repetir uno para causar conflicto
        # Para simular la concurrencia, algunos usuarios intentarán reservar el mismo asiento
        if i < len(asientos_disponibles) and random.random() > (porcentaje_conflicto / 100):
            asiento = random.choice(asientos_disponibles)
            asientos_disponibles.remove(asiento)  # Quitar asiento para no volver a seleccionarlo
        else:
            # Intentar un asiento que podría ya estar seleccionado (simular conflicto)
            if asientos_disponibles:
                asiento = random.choice(asientos_disponibles)
            else:
                # Si no quedan asientos disponibles, escoge uno aleatorio (que causará conflicto)
                max_asiento = 50  # Valor por defecto
                try:
                    conexion = psycopg2.connect(**CONFIG_BD)
                    cursor = conexion.cursor()
                    cursor.execute("SELECT MAX(numero_asiento) FROM asientos WHERE id_evento = %s;", (id_evento,))
                    max_result = cursor.fetchone()[0]
                    if max_result:
                        max_asiento = max_result
                    cursor.close()
                    conexion.close()
                except:
                    pass
                asiento = random.randint(1, max_asiento)
        
        print(f"➡️ Usuario {id_usuario} intentará reservar el asiento {asiento}")
        
        # Crea el hilo para la reserva
        hilo = threading.Thread(
            target=reservar_asiento,
            args=(id_usuario, id_evento, asiento, niveles_aislamiento[aislamiento], resultados)
        )
        
        hilos.append(hilo)
        hilo.start()
        time.sleep(0.05)  # Pequeña pausa entre lanzamientos de hilos
    
    # Espera a que todos los hilos terminen
    for hilo in hilos:
        hilo.join()
    
    tiempo_total_global = time.time() - tiempo_inicio_global
    
    # Analizar resultados
    exitosas = sum(1 for r in resultados if r['exito'])
    fallidas = numero_usuarios - exitosas
    tiempo_promedio = sum(r['tiempo'] for r in resultados) / len(resultados) if resultados else 0
    
    print("\n===== RESULTADOS =====")
    print(f"Nivel de aislamiento: {aislamiento}")
    print(f"Usuarios concurrentes: {numero_usuarios}")
    print(f"Reservas exitosas: {exitosas}")
    print(f"Reservas fallidas: {fallidas}")
    print(f"Tiempo promedio por reserva: {tiempo_promedio:.2f} ms")
    print(f"Tiempo total de la simulación: {tiempo_total_global:.2f} segundos")
    print("=====================\n")
    
    return {
        'usuarios': numero_usuarios,
        'nivel_aislamiento': aislamiento,
        'reservas_exitosas': exitosas,
        'reservas_fallidas': fallidas,
        'tiempo_promedio': tiempo_promedio
    }

# Función para realizar todas las pruebas requeridas
def ejecutar_todas_pruebas(id_evento):
    resultados = []
    
    # Pruebas requeridas según la especificación
    configuraciones = [
        {'usuarios': 5, 'aislamiento': 'READ COMMITTED'},
        {'usuarios': 10, 'aislamiento': 'REPEATABLE READ'},
        {'usuarios': 20, 'aislamiento': 'SERIALIZABLE'},
        {'usuarios': 30, 'aislamiento': 'SERIALIZABLE'}
    ]
    
    for config in configuraciones:
        resultado = ejecutar_simulacion(
            numero_usuarios=config['usuarios'],
            aislamiento=config['aislamiento'],
            id_evento=id_evento
        )
        if resultado:
            resultados.append(resultado)
            time.sleep(1)  # Pausa entre pruebas
    
    # Generar tabla de resultados en formato adecuado para el informe
    print("\n===== TABLA DE RESULTADOS PARA EL INFORME =====")
    print("| Usuarios | Nivel de Aislamiento | Reservas Exitosas | Reservas Fallidas | Tiempo Promedio |")
    print("|----------|----------------------|-------------------|-------------------|-----------------|")
    for r in resultados:
        print(f"| {r['usuarios']:8} | {r['nivel_aislamiento']:20} | {r['reservas_exitosas']:17} | {r['reservas_fallidas']:17} | {r['tiempo_promedio']:.2f} ms {' ':8} |")
    print("================================================\n")

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
