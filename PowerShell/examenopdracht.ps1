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

# Create "groups" and "users" OUs inside "s121517"
$groupsOUPath = "OU=groups,$s121517OUPath"
$usersOUPath = "OU=users,$s121517OUPath"
$groupsOUExists = Invoke-Command -Session $remoteADSession -Command {Get-ADOrganizationalUnit -Filter 'Name -eq "groups"' -SearchBase $s121517OUPath}
$usersOUExists = Invoke-Command -Session $remoteADSession -Command {Get-ADOrganizationalUnit -Filter 'Name -eq "users"' -SearchBase $s121517OUPath} 

if (-not $groupsOUExists) {
    Invoke-RemoteCommand -Command "New-ADOrganizationalUnit -Name 'groups' -Path '$s121517OUPath'" -ErrorAction SilentlyContinue
}

if (-not $usersOUExists) {
    Invoke-RemoteCommand -Command "New-ADOrganizationalUnit -Name 'users' -Path '$s121517OUPath'" -ErrorAction SilentlyContinue
}

# Get all groups where the AzureAD user "s121517" is a member
$azureADUser = Get-AzureADUser -Filter "UserPrincipalName eq 's121517@ap.be'"
$azureADGroups = Get-AzureADUserMembership -ObjectId $azureADUser.ObjectId | Where-Object { $_.ObjectType -eq "Group" }

# Copy the groups to the "groups" OU in the remote AD server
foreach ($group in $azureADGroups) {
    $groupName = $group.DisplayName
    $groupScope = "Universal"
    $groupCategory = "Distribution"
    Invoke-Command -Session $remoteADSession -ScriptBlock {New-ADGroup -Name $Using:groupName -GroupCategory $Using:groupCategory -GroupScope $Using:groupScope -Path $Using:groupsOUPath -ErrorAction SilentlyContinue} 
}

# Copy users of each group to the "users" OU in the remote AD server
foreach ($group in $azureADGroups) { 
    $azureADGroupMembers = Get-AzureADGroupMember -ObjectId $group.ObjectId -Top 5 | Where-Object { $_.ObjectType -eq "User" }
    $groupParams = @{ 
        Identity = "CN=$($group.DisplayName),$groupsOUPath"
        Server = "PFSV1NG.PoliFormaNG.local"
    }
    

    foreach ($member in $azureADGroupMembers) {
        
        
            # Create user in the "users" OU
            $Name = $member.DisplayName
            $DisplayName = $member.DisplayName
            $SamAccountName = $member.UserPrincipalName.Split('@')[0]
            $GivenName = $member.GivenName
            $SurName = $member.Surname
            $UserPrincipalName = $member.UserPrincipalName
            Invoke-Command -Session $remoteADSession -Command {New-ADUser -Name $Using:Name -DisplayName $Using:DisplayName -SamAccountName $Using:SamAccountName -GivenName $Using:GivenName -Surname $Using:SurName -UserPrincipalName $Using:UserPrincipalName -Path $Using:usersOUPath -ErrorAction SilentlyContinue}
            
            $userParams = @{
                Identity = "CN=$($member.DisplayName),$usersOUPath"
                Server = "PFSV1NG.PoliFormaNG.local"
            }
            

            # Add user to the corresponding group in the remote AD server
            Invoke-Command -Session $remoteADSession -ScriptBlock {Add-ADGroupMember -Identity (Get-ADGroup @Using:groupParams) -Members (Get-ADUser @Using:userParams) -Server "PFSV1NG.PoliFormaNG.local"}
            
    }
}

# Disconnect from the AzureAD cloud environment
Disconnect-AzureAD

# Close the remote AD server session
Remove-PSSession $remoteADSession