import network
import socket
import time
import random
from machine import Pin, ADC, I2C
from stemma_soil_sensor import StemmaSoilSensor

SDA_PIN = 4 # GPIO 4 
SCL_PIN = 5 # GPIO 5


i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)

time.sleep(2)
stemma_soil_sensor = StemmaSoilSensor(i2c)
seesaw = stemma_soil_sensor # Data Sheet = ~200 (very dry) to ~2000 (very wet) 1015 = Wet, 331 = Dry
time.sleep(2)

pump = Pin(16, Pin.OUT)
pump.value(0)
pump_state = False

light = Pin(15, Pin.OUT)
light.value(0)
light_state = False

photo_res = ADC(Pin(27))
garden_state = True
garden_state_readable = "Automated"



ssid = "Droid"
password = "password123"

def webpage(pump_state, garden_state, garden_state_readable, moisture):
    if not garden_state:
        manual_mode_html = f'''<br>
    <br>
    <div class="operation-mode" style="justify-content: space-around;">
        <div class="box1">
            <h3>Pump State: {pump_state}</h3>
            <a href="pumpon"><button class="btn">On</button></a>
            <a href="pumpoff"><button class="btn">Off</button></a> 
        </div>
        <div class="box2">
            <h3>Grow Light State: {light_state}</h3>
            <a href="lighton"><button class="btn">On</button></a>
            <a href="lightoff"><button class="btn">Off</button></a> 
        </div>
    </div>
        '''
    else:
        manual_mode_html = ""

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Indoor Garden</title>
</head>
<body>
    <br>
    <h1 id="title">Welcome to your Indoor Garden!</h1>
    <br>
    <div class="operation-mode">
        <h3>Current Operation mode: {garden_state_readable}</h3>
        <a href="automated"><button class="btn">Automated</button></a>
        <a href="manual"><button class="btn">Manual</button></a>
        <h2 id="moisture-value">Moisture {moisture}</h2>
    </div>
    <button onclick="loadMoistureValue()"> LOAD MOISTURE </button>

    {manual_mode_html}

</body>

<style>
    :root{{
        --brown: #8D6E63;
        --light-green: #52d656;
        --dark-green: #219c27;
    }}

    .box1{{
        display: inline-block;
        border-color: #388E3C;
        border-width: 2px;
        border-style: double;
        padding: 10px;
        margin-right: 20px;
    }}

    .box2{{
        display: inline-block;
        border-color: #388E3C;
        border-width: 2px;
        border-style: double;
        padding: 10px;
        margin-left: 20px;

    }}

    body{{
        background-color: var(--brown);
    }}

    .operation-mode{{
        background-color: var(--light-green);
        margin-left: 20%;
        margin-right: 20%;
        text-align: center;
        padding: 20px;
        border-color: #9aff9d;
        border-width: 2px;
        border-style: dashed;
    }}
    
    #title{{
        text-align: center; 
        color: whitesmoke;
        text-shadow: 5px 5px 3px #000000;
    }}

    .btn{{
        border-radius: 50%;
        padding: 10px;
        border-color: #388E3C;
        background-color: var(--dark-green)
    }}
</style>
<script>
function loadMoistureValue(){{
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {{
        document.getElementById("moisture-value").innerHTML = this.responseText;
        
    }}
    xhttp.open("GET", "/moisture", true);
    xhttp.send();
}}

</script>
</html>
    '''

    return str(html)


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)


connection_timeout = 10

while connection_timeout > 0:
    if wlan.status() >= 3:
        break
    connection_timeout -= 1
    print("Attempting to connect to wifi!")
    time.sleep(1)


if wlan.status() != 3:
    raise RuntimeError("Could not connect... :(")
else:
    print("Connected!")
    network_information = wlan.ifconfig()
    print("IP: ", network_information[0])

address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(address)
s.listen()

print("Listening on: ", address)

while True:
    try:
        conn, address = s.accept()
        print("Got connection from: ", address)

        request = str(conn.recv(1024))
        print("Req content: ", request)

        try:
            request = request.split()[1]
            print("Request: ", request)
        except IndexError:
            pass

        if request == "/pumpon":
            pump.value(1)
            print("Pump on")
            pump_state = True

        elif request == "/pumpoff":
            pump.value(0)
            print("Pump off")
            pump_state = False

        elif request == "/lighton":
            light.value(1)
            print("light on")
            light_state = True

        elif request == "/lightoff":
            light.value(0)
            print("light off")
            light_state = False

        elif request == "/automated":
            print("running in automated mode")
            garden_state = True
            garden_state_readable = "Automated"

        elif request == "/manual":
            print("Running in manual mode")
            garden_state = False
            garden_state_readable = "Manual"

        elif request == "/moisture":
            moisture = seesaw.get_moisture()
            temperature = seesaw.get_temp()
            resp = (str(moisture))
            conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            conn.send(resp)
            conn.close()
            


        resp = webpage(pump_state, garden_state, garden_state_readable, 0)
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        conn.send(resp)
        conn.close()
        


    except OSError as e:
        conn.close()
        print("Connection closed")
