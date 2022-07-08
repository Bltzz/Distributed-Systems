import glob
import json
import os.path
import paramiko

# Load config file
try:
    with open('.ftp_config.json') as json_file:
        config = json.load(json_file)
except FileNotFoundError:
    print('.ftp_config.json misses')
    exit()


# Connect to each host, then upload the contents of the provided folder names
# If the folder doesn't exist, then create the folder.
# Does not do subdirectories
def ftp(host):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=config['username'], password=config['password'], timeout=2)
        sftp = ssh.open_sftp()
        print_string = host + ' - put'

        for folder in config['folders']:
            for file in glob.glob(folder + '/*'):
                basename = os.path.basename(file)
                if not basename.__contains__("broadcast") and not basename.__contains__("unicast") and not basename.__contains__("Middleware"):
                    print(basename)
                    try:
                        if not basename.__contains__("__pycache__"):
                            sftp.put(file, f'{config["path"]}/{folder}/{basename}')
                    except FileNotFoundError:
                        sftp.mkdir(f'{config["path"]}/{folder}')
                        sftp.put(file, f'{config["path"]}/{folder}/{basename}')
                    print_string += ' ' + folder + "/" + basename

        print(print_string)
        sftp.close()
    except TimeoutError:
        print(host, '- Connection Timeout')


if __name__ == '__main__':
    for server in config['servers']:
        ftp(server)
