import network
import socket
import time
import random
from machine import Pin


pump = Pin(16, Pin.OUT)
pump_state = False

ssid = "Woodside"
password = "172-Wood"

def webpage(pump_state):
    html = f'''<h1>Grass Grower &#128511;</h1>
        <h3>Pump<h3>
        <h4>{pump_state}<h4>
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
            print("light on")

        elif request == "/lightoff":
            print("light off")

        elif request == "/automated":
            print("running in automated mode")

        elif request == "/manual":
            print("Running in manual mode")


        resp = webpage(pump_state)
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        conn.send(resp)
        conn.close()

    except OSError as e:
        conn.close()
        print("Connection closed")
