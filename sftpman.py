#!/usr/bin/python

import sys		

if __name__ == "__main__":
	if len(sys.argv) == 1:
		import sftpman.GUI
		sftpman.GUI.start()
	else:
		import sftpman.CLI
		sftpman.CLI.start()
