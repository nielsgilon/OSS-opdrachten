#!/usr/bin/python3


import argparse
import csv
import os
import subprocess
import sys
import crypt

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Create users from a CSV file, create groups specified with a file or as arguments or delete users')
parser.add_argument('-c', '--create', metavar='csv_file', type=str,
                    help='Create users from the specified CSV file')
parser.add_argument('-g', '--group', help='Name of the group to be created')
group = parser.add_mutually_exclusive_group()
group.add_argument('-f', '--file', help='CSV file containing usernames')
group.add_argument('users', nargs='*', default=[], help='List of usernames (if -f is not specified)')
args = parser.parse_args()

if args.create:
    
    # Read the CSV file
    with open(args.create, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')


        # Check if the class group exists, and create it if it doesn't

        try:
            subprocess.run(['getent', 'group', 'students'], check=True)
        except subprocess.CalledProcessError:
                subprocess.run(['groupadd', 'students'], check=True)

        for row in reader:
            # Extract the username and group name from the CSV file
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
            
            # Create SSH directory and authorized_keys file if they don't exist
            print(f"home_dir: {home_dir}")
            ssh_dir = os.path.join(home_dir, '.ssh')
            print(f"ssh_dir: {ssh_dir}")
            authorized_keys_file = os.path.join(ssh_dir, 'authorized_keys')

            if not os.path.exists(ssh_dir):
                os.makedirs(ssh_dir, mode=0o700)
                subprocess.run(['chown', '-R', f'{username}:{groupname}', ssh_dir], check=True)
                subprocess.run(['chmod', '700', ssh_dir], check=True)
                print(ssh_dir)

            if not os.path.exists(authorized_keys_file):
                with open(authorized_keys_file, 'w') as f:
                    f.write('')  # Write an empty string as the content
                    subprocess.run(['chown', '-R', f'{username}:{groupname}', authorized_keys_file], check=True)
                    subprocess.run(['chmod', '644', authorized_keys_file], check=True)
                    print(authorized_keys_file)

            # Append public key to authorized_keys file if it's empty
            if os.path.getsize(authorized_keys_file) == 0:
                with open(authorized_keys_file, 'a') as f:
                    f.write(public_key + '\n')
                    
            print(f"User {username} created successfully.")


if args.group:

    group_name = args.group

    # Create group
    try:
        subprocess.run(['groupadd', group_name], check=True)
        print(f"Group '{group_name}' created successfully.")
    except subprocess.CalledProcessError:
        print(f"Group '{group_name}' already exists.")

    # Add users to the group
    if args.file:
       
        with open(args.file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                username = row['studentid']
                try:
                    subprocess.run(['usermod', '-a', '-G', group_name, username], check=True)
                    print(f"User '{username}' added to group '{group_name}'.")
                except subprocess.CalledProcessError:
                    print(f"User '{username}' does not exist.")
    else:
        username = args.users
        try:
            subprocess.run(['usermod', '-a', '-G', group_name, username], check=True)
            print(f"User '{username}' added to group '{group_name}'.")
        except subprocess.CalledProcessError:
            print(f"User '{username}' does not exist.")


else:
    print(f"Please specify either the options -c/--create, -g/--group or -d/--delete with required arguments")