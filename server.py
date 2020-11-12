from lanchat import networking

print('Press Enter to exit')
srv = networking.Server()
srv.bind('127.0.0.1', 9090)

input()
srv.close()
