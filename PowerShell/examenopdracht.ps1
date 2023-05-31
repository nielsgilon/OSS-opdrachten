Clear-Host

Import-Module AzureAD

# Connect to the remote AD server
$remoteADSession = New-PSSession -ComputerName PFSV1NG -UseSSL -Credential (Get-Credential)

# Connect to the AzureAD cloud environment
Connect-AzureAD

# Invoke command on the remote AD server
function Invoke-RemoteCommand {
    param (
        [string]$Command
    )
    Invoke-Command -Session $remoteADSession -ScriptBlock { param($Command) Invoke-Expression $Command } -ArgumentList $Command
}

# Create "OS_Scripting_23" OU if it doesn't exist
$ouPath = "OU=OS_Scripting_23,DC=PoliFormaNG,DC=local"
$ouExists = Invoke-Command -Session $remoteADSession -Command {Get-ADOrganizationalUnit -Filter 'Name -like "OS_Scripting_23"'}

if (-not $ouExists) {
    Invoke-RemoteCommand -Command "New-ADOrganizationalUnit -Name 'OS_Scripting_23' -Path 'DC=PoliFormaNG,DC=local'" -ErrorAction SilentlyContinue
}

# Create "s121517" OU inside "OS Scripting 23"
$s121517OUPath = "OU=s121517,$ouPath"
$s121517OUExists = Invoke-Command -Session $remoteADSession -Command {Get-ADOrganizationalUnit -Filter 'Name -eq "s121517"' -SearchBase $ouPath}

if (-not $s121517OUExists) {
    Invoke-RemoteCommand -Command "New-ADOrganizationalUnit -Name 's121517' -Path '$ouPath'" -ErrorAction SilentlyContinue
}