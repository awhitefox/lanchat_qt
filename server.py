from lanchat import networking

srv = networking.Server()
srv.bind('127.0.0.1', 9090)

input("Press Enter to kill\n")
srv.close()
