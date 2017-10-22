import sys
import file_util


if __name__ == '__main__':
    print('cmd_launcher', sys.argv[1])
    file_util.rename_files(sys.argv[1])