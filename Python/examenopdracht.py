#!/usr/bin/python3

# aanmaken van argument parser voor de optie -c | --create
import argparse #importeer module argparse om gebruik te maken van zijn functies
import sys #importeer module sys om gebruik te maken van zijn functies

import csv #importeer module csv om csv files in te lezen mogelijk te maken

parser = argparse.ArgumentParser(description='maak gebruikers aan van een CSV file.') #maak de argument parser aan
parser.add_argument('-c', '--create', metavar='csv file', type=str,                   #voeg argument -c en --create toe plus metavar --> dit om de help statement meer leesbaar te maken bv -c csv file en --create csv file
                    help='maak gebruikers aan van de gespecifieerde CSV file')        #description voor help statement
args = parser.parse_args()                                                            #parser oproepen voor gebruik

if not args.create:                                                                   #argument gebruiken in if statement
    print("Specifieer alstublieft een csv file na de optie -c of --create.")          #als het argument oningevuld blijft print deze output op de terminal
    sys.exit(1)                                                                       #exit code 1 om te indiceren dat een error is opgetreden als de plaats van het argument leeg blijft

# lees de csv file in
with open(args.create, newline='') as csvfile:                                        #def open om gespecifieerde file te openen geeft nieuwe variabele csvfile ipv args.creat                                                       
    reader = csv.DictReader(csvfile, delimiter=';')                                   #csv.dictreader van variabele csvfile als nieuwe variabele 'reader' om door te loopen
                                                                                      #belangrijk! delimiter als ';' ingesteld = teken dat values separate in mijn csv file
    for row in reader:                                                                #door de file loopen
        # gebruikers informatie van de csv file ophalen en word in variabele gestoken om later te gebruiken
        gebruikersnaam = row['studentid']                                             #per iteratie in csv bestand 4 variabelen aanmaaken
        wachtwoord = row['wachtwoord']                                                
        groepnaam = row['klasgroep']
        public_key = row['public_key']
        email = row['email']
        home_dir = '/home/' + email.split('@')[0]                            #de home directory moest /home/"alles voor het @ teken in email adres zijn"