from machine import I2C, Pin
import time

class I2cLcd:
    # Comandos LCD
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80

    # Flags para visualización on/off
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00

    # Flags para configuración de display
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00

    def __init__(self, i2c, addr, cols, rows):
        self.i2c = i2c
        self.addr = addr
        self.cols = cols
        self.rows = rows
        self.backlight = True
        self.display_control = self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF
        
        # Inicializar display
        self._write_command(0x03)
        time.sleep_ms(5)
        self._write_command(0x03)
        time.sleep_ms(5)
        self._write_command(0x03)
        time.sleep_ms(1)
        self._write_command(0x02)
        
        # Configurar LCD para 4-bit mode, 2 líneas, tipo de fuente
        self._write_command(self.LCD_FUNCTIONSET | self.LCD_4BITMODE | self.LCD_2LINE | self.LCD_5x8DOTS)
        
        # Encender display, cursor off, blink off
        self._write_command(self.LCD_DISPLAYCONTROL | self.display_control)
        
        # Limpiar display
        self.clear()
        
        # Establecer dirección y dirección de movimiento del cursor
        self._write_command(self.LCD_ENTRYMODESET | 0x02)

    def _write_command(self, cmd):
        # Enviar comando a la LCD sin RS (Register Select)
        self._write(cmd, 0)

    def _write_data(self, data):
        # Enviar datos a la LCD con RS (Register Select)
        self._write(data, 1)

    def _write(self, data, rs):
        b = bytearray(1)
        b[0] = data & 0xF0
        if rs:
            b[0] |= 0x01
        if self.backlight:
            b[0] |= 0x08
            
        self.i2c.writeto(self.addr, b)
        self._pulse_enable(b[0])
        
        b[0] = (data << 4) & 0xF0
        if rs:
            b[0] |= 0x01
        if self.backlight:
            b[0] |= 0x08
            
        self.i2c.writeto(self.addr, b)
        self._pulse_enable(b[0])

    def _pulse_enable(self, data):
        b = bytearray(1)
        b[0] = data | 0x04  # EN=1
        self.i2c.writeto(self.addr, b)
        time.sleep_us(1)
        b[0] = data & ~0x04  # EN=0
        self.i2c.writeto(self.addr, b)
        time.sleep_us(50)

    def clear(self):
        # Limpiar la pantalla y volver a posición inicial
        self._write_command(self.LCD_CLEARDISPLAY)
        time.sleep_ms(2)

    def home(self):
        # Volver a posición inicial
        self._write_command(self.LCD_RETURNHOME)
        time.sleep_ms(2)

    def set_cursor(self, col, row):
        # Establecer la posición del cursor
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        self._write_command(self.LCD_SETDDRAMADDR | (col + row_offsets[row]))

    def no_display(self):
        # Apagar display
        self.display_control &= ~self.LCD_DISPLAYON
        self._write_command(self.LCD_DISPLAYCONTROL | self.display_control)

    def display(self):
        # Encender display
        self.display_control |= self.LCD_DISPLAYON
        self._write_command(self.LCD_DISPLAYCONTROL | self.display_control)

    def no_cursor(self):
        # Ocultar cursor
        self.display_control &= ~self.LCD_CURSORON
        self._write_command(self.LCD_DISPLAYCONTROL | self.display_control)

    def cursor(self):
        # Mostrar cursor
        self.display_control |= self.LCD_CURSORON
        self._write_command(self.LCD_DISPLAYCONTROL | self.display_control)

    def no_blink(self):
        # Apagar parpadeo del cursor
        self.display_control &= ~self.LCD_BLINKON
        self._write_command(self.LCD_DISPLAYCONTROL | self.display_control)

    def blink(self):
        # Encender parpadeo del cursor
        self.display_control |= self.LCD_BLINKON
        self._write_command(self.LCD_DISPLAYCONTROL | self.display_control)

    def backlight_on(self):
        # Encender la luz de fondo
        self.backlight = True
        self.i2c.writeto(self.addr, bytearray([0x08]))

    def backlight_off(self):
        # Apagar la luz de fondo
        self.backlight = False
        self.i2c.writeto(self.addr, bytearray([0x00]))

    def print(self, text):
        # Imprimir texto en la posición actual
        for char in text:
            self._write_data(ord(char))


# Función de utilidad para escanear dispositivos I2C
def scan_i2c_devices(i2c):
    print("Escaneando dispositivos I2C...")
    devices = i2c.scan()
    if devices:
        for device in devices:
            print("Dispositivo encontrado en dirección: 0x{:02X}".format(device))
        return devices
    else:
        print("No se encontraron dispositivos I2C")
        return []