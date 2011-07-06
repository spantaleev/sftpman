#!/usr/bin/python

# launcher.main() is called by the sftpman executable (look at setup.py)
def main():
    import sys, os
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.append(path)
    from sftpman import cli
    cli.start()

if __name__ == '__main__':
    main()
