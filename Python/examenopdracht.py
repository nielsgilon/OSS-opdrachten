#!/usr/bin/python3


import argparse
import csv
import os
import subprocess
import sys
import crypt

#Check if user has root privileges, exit and prompt if not
if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Create users from a CSV file, create groups specified with a file or as arguments or delete users')
parser.add_argument('-c', '--create', metavar='csv_file', type=str,
                    help='Create users from the specified CSV file')
parser.add_argument('-g', '--group', help='Name of the group to be created')
group = parser.add_mutually_exclusive_group()
group.add_argument('-f', '--file', help='CSV file containing usernames')
group.add_argument('users', nargs='*', type=str, default=[''], help='List of usernames (if -f is not specified)')
parser.add_argument('-d', '--delete', action='store_true',help='Delete specified users using options')
deleterequired = parser.add_argument_group()
deleterequired.add_argument('-i', '--interactive', action='store_true', help='Ask for permision before deleting users', required=False)
args = parser.parse_args()

if args.delete and not args.interactive:
    parser.error('The subargument -i or --interactive is mandatory when selecting the optional argument -d or --delete')

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

    # Create specified group 
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
        usernames = args.users
        for username in usernames:
            try:
                subprocess.run(['usermod', '-a', '-G', group_name, username], check=True)
                print(f"User '{username}' added to group '{group_name}'.")
            except subprocess.CalledProcessError:
                print(f"User '{username}' does not exist.")

if args.delete:

    # Get all users in the students group
    studenten_users = subprocess.check_output(['getent', 'group', 'students']).decode().split(':')[3].split(',')

    # Get all users who's username starts with 's'
    s_users = subprocess.check_output(['getent', 'passwd']).decode().split('\n')
    s_users = [user.split(':')[0] for user in s_users if user.startswith('s')]

    #Combine into a list of users to be deleted
    users_to_delete = studenten_users + s_users

    if args.interactive:
            print("The following users will be deleted:")
            print("\n".join(users_to_delete))
            print()

            # Prompt the user for deletion choice
            print("Choose an action:")
            print("1. Delete all presented users.")
            print("2. Delete no users (abort).")
            print("3. Loop through every user and ask if they need to be removed.")
            choice = input("Enter your choice (1, 2, or 3): ")

            if choice == '1':
                for user in users_to_delete:
                    subprocess.call(['userdel', '-r', user])
            elif choice == '2':
                print("Aborted. No users will be deleted.")
                pass
            elif choice == '3':
                for user in users_to_delete:
                    answer = input(f"Do you want to delete user '{user}'? (y/n): ")
                    if answer.lower() == 'y':
                        subprocess.call(['userdel', '-r', user])
    else:
        for user in users_to_delete:
                    subprocess.call(['userdel', '-r', user])
    



else:
    print(f"Please specify either the options -c/--create, -g/--group or -d/--delete with required subarguments")