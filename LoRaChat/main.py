import serial
import serial.tools.list_ports

import socketserver
from flask import Flask, render_template, request, make_response
import random
from collections import deque

global ser

MY_USERNAME = None # Your Username
MY_ADDRESS = None # Your Address
FREQUENCY = 470000000
CRLF = "\r\n"
SEP = ","
MAX_MESSAGES = 10 # Maximum number of messages contained by the queue
REC_USERNAME = None # Receiver Username
REC_ADDRESS = None # Receiver address

ser = None
try:
    ports = serial.tools.list_ports.comports()
    port = random.choice(ports)
    ser = serial.Serial(
    port=port.device,\
    baudrate=115200,\
    parity=serial.PARITY_NONE,\
    stopbits=serial.STOPBITS_ONE,\
    bytesize=serial.EIGHTBITS,\
    timeout=0)
except:
    print("serial error")
    exit()
# message queue
message_queue = deque()

def read_data(ser):
    line = []
    while True:
        c = ser.read()
        line.append(c.decode("UTF-8"))
        if c == b'\n':
            line = ''.join(line)
            break
    print(line)
    return line


def set_frequency(ser):
    print("setting up serial device")
    command = "AT+BAND=" + str(FREQUENCY) + CRLF
    ser.write(command.encode())
    while(not "OK" in read_data(ser)):
        pass 
    
    command = "AT+BAND?" + CRLF
    ser.write(command.encode())
    while(not "BAND" in read_data(ser)):
        pass 
    
    
def LoRaReset(ser):
    command = "AT+RESET" + CRLF
    print(command.encode())
    ser.write(command.encode())
    while(not "OK" in read_data(ser) or not not "RESET" in read_data(ser)):
        pass


def handle_serial_message(message: str):
    if "+RCV" in message:
        length = int(message.split(",")[1])
        if length > 0:
            data = REC_USERNAME + ": " + message.split(",")[2]
            update_queue(data)
            
  
# thread listening to messages asyncronously
def listen_serial():
    while True:
        message = read_data(ser)
        handle_serial_message(message)  


try:

    print("connected to: " + ser.portstr)
    set_frequency(ser)
    
    # infinite thread for reading from serial
    import threading
    t = threading.Thread(target=listen_serial)
    t.daemon = False
    t.start()
    
except:
    print("Could not find any Serial port available, or could not open it")
    exit()
    
app = Flask(__name__, template_folder='templates')
    
        
def update_queue(data: str):
    if len(message_queue) > MAX_MESSAGES:
        message_queue.popleft()
    
    message_queue.append(data)


@app.route('/', methods=['GET', 'POST'])
def index():
    global MY_USERNAME
    global MY_ADDRESS
    global REC_USERNAME
    global REC_ADDRESS
    
    MY_USERNAME = request.cookies.get('MyUsername')
    MY_ADDRESS = request.cookies.get('MyAddress')
    REC_USERNAME = request.cookies.get('RecUsername')
    REC_ADDRESS = request.cookies.get('RecAddress')
    
    if MY_USERNAME and MY_ADDRESS and REC_USERNAME and REC_ADDRESS:
        return render_template('chat.html', message_list=message_queue)
        
    if request.method == 'POST':
        MY_USERNAME = request.form['MyUsername']
        MY_ADDRESS = request.form['MyAddress']
        REC_USERNAME = request.form['RecUsername']
        REC_ADDRESS = request.form['RecAddress']
        
        set_address(ser)
        
        # Setting cookies
        resp = make_response(render_template('chat.html', message_list=message_queue))
        resp.set_cookie('MyUsername', MY_USERNAME)
        resp.set_cookie('MyAddress', MY_ADDRESS)
        resp.set_cookie('RecUsername', REC_USERNAME)
        resp.set_cookie('RecAddress', REC_ADDRESS)
        return resp
    else:
        return render_template('index.html', message_list=message_queue)


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        input_string = request.form['chat']
        
        if input_string is not None and input_string != "":
            input_string = MY_USERNAME + ": " + input_string
            write_data(ser, input_string)
            update_queue(input_string)
    return render_template('chat.html', message_list=message_queue)
   
    
def set_address(ser):
    command = "AT+ADDRESS=" + str(MY_ADDRESS) + CRLF
    ser.write(command.encode())
    while(not "OK" in read_data(ser)):
        pass

    command = "AT+ADDRESS?" + CRLF
    ser.write(command.encode())
    while(not "ADDRESS" in read_data(ser)):
        pass 


def write_data(ser, data: str):
    assert len(data) < 240, "payload is too large"
    command = "AT+SEND=" + str(REC_ADDRESS) + SEP + str(len(data)) + SEP + data + CRLF
    print(command)
    ser.write(command.encode())


if __name__ == '__main__':
    assert ser is not None, "Could not initialize serial port"

    try:
        with socketserver.TCPServer(('localhost', 5000), socketserver.BaseRequestHandler) as httpd:
            app.run(host='localhost', port=5000, threaded=True, debug=False, use_reloader=False)
            httpd.server_close()
    except KeyboardInterrupt:
        print("Programma interrotto dall'utente")
    finally:
        ser.close()