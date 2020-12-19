import os
import pathlib

# Interactive backup-script for copying backup_src to backup_dest.
# For all files >= MIN_SIZE, the user is prompted [include / exclude / step into]
# All smaller files are copied anyway

# Parameters, use absolute paths
MIN_SIZE = 5000000  # (5MB)
backup_src = ""  # e.g. /home/schmina
backup_dest = ""  # e.g. /media/external_harddrive/backup_june20

# ================================================

def print_bytes_human(fileSize):
    for count in ['B', 'KB', 'MB', 'GB']:
        if fileSize > -1024.0 and fileSize < 1024.0:
            return "%3.1f%s" % (fileSize, count)
        fileSize /= 1024.0
    return "%3.1f%s" % (fileSize, 'TB')


def get_directory_size(directory):  # in bytes
    total = 0
    try:
        for entry in os.scandir(directory):
            if entry.is_dir():
                total += get_directory_size(entry.path)
            elif os.path.islink(directory):
                continue
            elif entry.is_file():
                total += entry.stat().st_size
    except NotADirectoryError:
        return os.path.getsize(directory)
    except PermissionError:
        return 0
    return total


def interactive_loop(curr_dir, excludelist):

    def abs_to_rel_path(somePath):
        prefix = len(backup_src)+1
        return somePath[prefix:]

    # get list of files (and their size) in current directory
    filelist = [elem.as_posix() for elem in pathlib.Path(curr_dir).glob('./*')]
    sorted_filelist = []
    for filename in filelist:
        if os.path.islink(filename):
            continue
        elif os.path.isdir(filename):
            sorted_filelist.append((filename, get_directory_size(filename)))
        else:
            sorted_filelist.append((filename, os.path.getsize(filename)))

    # Sort entries by size
    sorted_filelist.sort(key=lambda x: x[1], reverse=True)

    # only need manual approval if file has certain size
    sorted_filelist = [x for x in sorted_filelist if x[1] >= MIN_SIZE]

    # let user decide
    for filename in sorted_filelist:
        if os.path.isdir(filename[0]):
            while True:
                answer = input("{} {} ( /n/r) ".format(filename[0], print_bytes_human(filename[1])))
                if answer == "n":
                    excludelist.write(abs_to_rel_path(filename[0]) + "\n")
                    break
                elif answer == "r":
                    interactive_loop(filename[0], excludelist)
                    break
                elif answer == "":
                    break
                else:
                    print("invalid input, try again")
        else:
            while True:
                answer = input("{} {} ( /n) ".format(filename[0], print_bytes_human(filename[1])))
                if answer == "n":
                    excludelist.write(abs_to_rel_path(filename[0]) + "\n")
                    break
                elif answer == "":
                    break
                else:
                    print("invalid input, try again")



print("backup script\n" + 20*"-")

if (not os.path.exists(backup_src)) or (not os.path.exists(backup_dest)):
    raise Exception("Error, source or target directory does not exist")

# remove potential trailing slash
backup_src = backup_src[:-1] if backup_src[-1] == "/" else backup_src
backup_dest = backup_dest[:-1] if backup_dest[-1] == "/" else backup_dest

exclude_file = "/tmp/exclude_dirs.txt"
file = open(exclude_file, "w").close()  # clear potential existing content
file = open(exclude_file, "a")

print("usage:\n   pressing just enter will include the file in the backup")
print("   character n will exclude a file/dir from the backup")
print("   character r steps into a directory and allows continuation from there")
print(20*"-")
interactive_loop(backup_src, file)
file.close()
print(20*"-")

print("first few lines of the file that contains files/dirs to be excluded:")
os.system("head -n 5 {} | sed 's/^/   /'".format(exclude_file))
print(20*"-")
command = """  sudo rsync -arv --exclude-from='{}' {} {}""".format(
    exclude_file, backup_src, backup_dest)
print("command to backup your files:\n", command)
print(20*"-")

if input("run the command now (y/n)? ") == "y":
    os.system(command)
else:
    print("aborted")
