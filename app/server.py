#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def send_history(self):
        print(f'Отправил историю = > {self.login}')
        # на случай если сообщений больше 10
        for massage in self.server.history[-10:] if len(self.server.history) > 10 else self.server.history:
            self.transport.write(f'{massage}'.encode())
            print(massage)

    def data_received(self, data: bytes):
        # print(data)
        decoded = data.decode(encoding='utf-8')

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("logon:", "").replace("\r\n", "")
                if self.login in self.server.nick:
                    self.transport.write(f"Логин {self.login} занят, попробуйте другой \n".encode())
                    #  - Отключать от сервера соединение клиента
                    self.server.clients.remove(self)
                    return
                else:
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode())
                    self.send_history()
                    self.server.nick.add(self.login)
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        users = [user for user in self.server.clients if user != self]
        # подправил что бы клиент не видел собственные сообщения
        for user in users:
            user.transport.write(message.encode())
        self.server.history.append(message)


class Server:
    clients: list  # экземпляры классов
    nick: set  # clients.login
    history: list

    def __init__(self):
        self.clients = []
        self.nick = set()
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
