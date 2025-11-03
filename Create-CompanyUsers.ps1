<#
.SYNOPSIS
Creates multiple local Windows users following the naming pattern <company>-user<number>.
Each user gets a password equal to their username and is added to the Administrators group.

.EXAMPLE
.\Create-CompanyUsers.ps1
#>

# Ensure script runs with admin privileges
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Please run this script as Administrator." -ForegroundColor Red
    exit
}

# Input: company prefix
$prefix = Read-Host "Enter company prefix (e.g. tcs)"
if ([string]::IsNullOrWhiteSpace($prefix)) {
    Write-Host "Prefix cannot be empty." -ForegroundColor Red
    exit
}

# Input: number of users
[int]$count = Read-Host "How many users to create (e.g. 10)"
if ($count -le 0) {
    Write-Host "Number must be greater than 0." -ForegroundColor Red
    exit
}

# Input: starting number (optional)
[int]$start = Read-Host "Starting number (default 1)"
if ($start -le 0) { $start = 1 }

Write-Host ""
Write-Host "Creating $count users with prefix '$prefix' starting from user$start..."
Write-Host ""

for ($i = 0; $i -lt $count; $i++) {
    $num = $start + $i
    $username = "$prefix-user$num"
    $password = $username

    # Check if user already exists
    if (Get-LocalUser -Name $username -ErrorAction SilentlyContinue) {
        Write-Host "[SKIP] User $username already exists." -ForegroundColor Yellow
        continue
    }

    try {
        # Create secure password
        $securePass = ConvertTo-SecureString $password -AsPlainText -Force

        # Create user
        New-LocalUser -Name $username -Password $securePass -FullName "$prefix User $num" -Description "$prefix employee user $num"

        # Add to Administrators group
        Add-LocalGroupMember -Group "Administrators" -Member $username

        Write-Host "[OK] Created user: $username (password: $password)" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Failed to create user $username : $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host " Done creating users."
Write-Host "All users have been added to the Administrators group."
Write-Host "Each password = username (e.g., tcs-user1)."
Write-Host "Consider forcing password change at first login for better security."
