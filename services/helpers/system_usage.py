import psutil


# Función para obtener el uso de CPU y Memori
def get_system_usage():
    cpu_percent = psutil.cpu_percent(interval=1)  # Uso de CPU en porcentaje
    memory_info = psutil.virtual_memory()  # Información sobre la memoria
    memory_percent = memory_info.percent  # Uso de memoria en porcentaje
    return cpu_percent, memory_percent
