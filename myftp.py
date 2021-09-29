import sys
from socket import socket, AF_INET, SOCK_STREAM

# get server name from command line
if len(sys.argv) != 2:
    print('Usage: myftp ftp_server_name')
    sys.exit()
server = sys.argv[1]

# create control connection socket
control_socket = socket(AF_INET, SOCK_STREAM)

# initiate control TCP connection
try:
    control_socket.connect((server, 21))
except Exception:
    print(f'Error: server {server} cannot be found.')
    sys.exit()
print(f'Connected to {server}.')

# print message from server
response = control_socket.recv(1024).decode('utf-8').strip()
print(response)

# send user name to server
username = input('Enter username: ')
control_socket.send(bytes(f'USER {username}\r\n', 'utf-8'))
response = control_socket.recv(1024).decode('utf-8').strip()
print(response)

# send password to server
password = input('Enter password: ')
control_socket.send(bytes(f'PASS {password}\r\n', 'utf-8'))
response = control_socket.recv(1024).decode('utf-8').strip()
print(response)

def extractPASVData(response):
    indexOne = response.index('(')
    indexTwo = response.index(')')
    return response[indexOne + 1:indexTwo].split(',')

def extractIP(data):
    return data[0] + '.' + data[1] + '.' + data[2] + '.' + data[3]

def extractPort(data):
    dataOne = int(data[4])
    dataTwo = int(data[5])

    return (dataOne * 256) + dataTwo

# login successful
if response.startswith('230'):
    # main loop
    loop = True
    while loop:
        userInput = input('ftp> ')
        listOfArgs = userInput.split()
        command = listOfArgs[0]

        if command == 'quit':
            # end session
            control_socket.send(bytes('QUIT\r\n', 'utf-8'))
            response = control_socket.recv(1024).decode('utf-8').strip()
            print(response)
            control_socket.close()
            loop = False

        elif command == 'put':
            # upload local file to remote server
            if (len(listOfArgs) != 2):
                print('Put command must be: put <filename>')
            else:
                filename = listOfArgs[1]
                try:
                    f = open(filename,'rb')
                except Exception:
                    print(f'Error: file {filename} not found')
                else:
                    control_socket.send(bytes('PASV\r\n', 'utf-8'))
                    response = control_socket.recv(1024).decode('utf-8').strip()
                    print(response)

                    data_socket = socket(AF_INET, SOCK_STREAM)
                    dataPASV = extractPASVData(response)
                    ip = extractIP(dataPASV)
                    port = extractPort(dataPASV)

                    try:
                        data_socket.connect((ip, port))
                    except Exception:
                        print(f'Error: server {ip} cannot be found.')
                    else:
                        print(f'Connected to data socket: {ip}')
                        control_socket.send(bytes(f'STOR {filename}\r\n', 'utf-8'))
                        response = control_socket.recv(1024).decode('utf-8').strip()
                        print(response)

                        print(f'Sending {filename} to {ip}')
                        l = f.read(1024)
                        while (l):
                            data_socket.send(l)
                            l = f.read(1024)
                        f.close()

                        data_socket.close()
                        response = control_socket.recv(1024).decode('utf-8').strip()
                        print(response)

        elif command == 'delete':
            # delete remote file from remote server
            filename = listOfArgs[1]
            control_socket.send(bytes(f'DELE {filename}\r\n', 'utf-8'))
            response = control_socket.recv(1024).decode('utf-8').strip()
            print(response)

        else:
            print(f'Error: command "{command}" not supported')