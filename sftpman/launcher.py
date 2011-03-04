#!/usr/bin/python

import sys		


def main():
	if len(sys.argv) == 1:
		import sftpman.GUI
		sftpman.GUI.start()
	else:
		import sftpman.CLI
		sftpman.CLI.start()
    

if __name__ == "__main__":
    main()
