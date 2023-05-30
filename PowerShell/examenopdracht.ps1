Clear-Host

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