#!/usr/bin/python3

import argparse #import argparse module for the command arguments
import csv #import csv module to read and extract info from csv file
import os #import os module to make use of its path functions
import subprocess #import subprocces module to make use off bash commands in the script
import sys #import sys module to use for troubleshooting purposes
import crypt #import crypt module to encrypt the plain text passwds from the csv file

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Create users from a CSV file.')
parser.add_argument('-c', '--create', metavar='csv_file', type=str,
                    help='Create users from the specified CSV file')
args = parser.parse_args()

if not args.create:
    print("Please specify a CSV file using the -c or --create option.")
    sys.exit(1)

# Read the CSV file
with open(args.create, newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')


    # Check if the class group exists, and create it if it doesn't

    try:
     subprocess.run(['getent', 'group', 'students'], check=True)
    except subprocess.CalledProcessError:
            subprocess.run(['groupadd', 'students'], check=True)

    for row in reader:
        # Extract the username and group name from the CSV file and stor in variables 
        username = row['studentid']
        password = row['wachtwoord']
        groupname = row['klasgroep']
        public_key = row['public_key']
        email = row['email']
        home_dir = '/home/' + email.split('@')[0]

        print(f"public_key: '{public_key}'")

        # Check if user already exists
        try:
            subprocess.check_call(['id', username], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
        # If the user doesn't exist, create the user and set password
            subprocess.run(['useradd', '-m', '-s', '/bin/bash', '-p', crypt.crypt(password),
                        username], check=True)
            
        # Set correct permissions and ownership for the user's new home directory
            # Check if the directory exists
            if os.path.exists(home_dir):
                subprocess.run(['rm', '-R', home_dir])
            else:
                subprocess.run(['usermod', '-d', home_dir, '-m', username], check=True)
                subprocess.run(['chown', '-R', f'{username}:{groupname}', home_dir], check=True)
                subprocess.run(['chmod', '700', home_dir], check=True)

        # Update the user's password using chpasswd
            password_input = f"{username}:{password}"
            subprocess.run(['chpasswd'], input=password_input.encode(), check=True)

        else:
            print(f"User {username} already exists, skipping...")
            continue

        # Check if the group exists, and create it if it doesn't
        try:
            subprocess.run(['getent', 'group', groupname], check=True)
        except subprocess.CalledProcessError:
            subprocess.run(['groupadd', groupname], check=True)