Clear-Host

# Connect to the remote AD server
New-PSSession -ComputerName PFSV1NG -UseSSL -Credential (Get-Credential)

# Connect to the AzureAD cloud environment
Connect-AzureAD