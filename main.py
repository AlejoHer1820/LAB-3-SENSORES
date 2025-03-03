from machine import Pin, SoftI2C, ADC, SPI
import time
from lcd_i2c import I2cLcd, scan_i2c_devices  # Importar la clase LCD

# Configuración de pines para MAX6675 (Termopar tipo K)
cs = Pin(27, Pin.OUT)
sck = Pin(12, Pin.OUT)
so = Pin(14, Pin.IN)

# Configuración del sensor LM35
lm35 = ADC(Pin(34))
lm35.atten(ADC.ATTN_11DB)  # Configuración para un rango de 0-3.3V

# Configuración del LCD I2C
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)

dispositivos = scan_i2c_devices(i2c)
if not dispositivos:
    print("No se encontraron dispositivos I2C. Revisa las conexiones.")
    while True:
        time.sleep(1)

LCD_ADDRESS = 0x27  # Cambiar si es necesario
LCD_ROWS = 2
LCD_COLS = 16
lcd = I2cLcd(i2c, LCD_ADDRESS, LCD_COLS, LCD_ROWS)

# Listas para almacenar lecturas y aplicar filtro de media móvil
buffer_termo = []
buffer_ambiente = []
BUFFER_SIZE = 5  # Tamaño del filtro de media móvil

# Función para leer el MAX6675
def read_max6675():
    cs.value(0)
    time.sleep(0.001)
    value = 0
    for i in range(16):
        sck.value(1)
        value <<= 1
        if so.value():
            value |= 1
        sck.value(0)
    cs.value(1)
    if value & 0x4:
        return None  # Error, termopar desconectado
    temp = (value >> 3) * 0.25
    return temp

# Función para leer el LM35 y calcular la temperatura ambiente
def read_lm35():
    voltage = lm35.read() * (3.3 / 4095.0)
    temp_c = voltage * 100
    return temp_c

# Función para aplicar filtro de media móvil
def filtro_media_movil(buffer, nueva_lectura):
    if len(buffer) >= BUFFER_SIZE:
        buffer.pop(0)  # Eliminar el valor más antiguo
    buffer.append(nueva_lectura)  # Agregar nueva lectura
    return sum(buffer) / len(buffer)  # Retornar promedio

# Mostrar mensaje de inicio
lcd.clear()
lcd.print("Iniciando...")
lcd.set_cursor(0, 1)
lcd.print("Sistema termopar")
time.sleep(2)

# Bucle principal
while True:
    temp_termo = read_max6675()
    temp_ambiente = read_lm35()

    lcd.clear()  # Limpiar la pantalla antes de mostrar nuevas lecturas

    if temp_termo is not None:
        temp_termo_filtrado = filtro_media_movil(buffer_termo, temp_termo)
        temp_ambiente_filtrado = filtro_media_movil(buffer_ambiente, temp_ambiente)
        temp_compensada = temp_termo_filtrado + (temp_ambiente_filtrado - 25)
        
        lcd.set_cursor(0, 0)
        lcd.print(f"Termo: {temp_compensada:.1f}C")
        lcd.set_cursor(0, 1)
        lcd.print(f"Amb: {temp_ambiente_filtrado:.1f}C")
        
        print(f'Temp Termopar: {temp_compensada:.1f}C | Temp Ambiente: {temp_ambiente_filtrado:.1f}C')
    else:
        lcd.set_cursor(0, 0)
        lcd.print("Error: No Termopar")
        print("Error: Termopar no conectado")
    
    time.sleep(0.5)