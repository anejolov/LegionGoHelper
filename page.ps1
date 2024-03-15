PARAM(
    [string]$Path,
    [int]$InitialSize,
    [int]$MaximumSize
)

$ComputerSystem = $null
$CurrentPageFile = $null
$modify = $false

# Disables automatically managed page file setting first
$ComputerSystem = Get-WmiObject -Class Win32_ComputerSystem -EnableAllPrivileges
if ($ComputerSystem.AutomaticManagedPagefile)
{
    $ComputerSystem.AutomaticManagedPagefile = $false
    $ComputerSystem.Put()
}

$CurrentPageFile = Get-WmiObject -Class Win32_PageFileSetting
if ($CurrentPageFile.Name -eq $Path)
{
    # Keeps the existing page file
    if ($CurrentPageFile.InitialSize -ne $InitialSize)
    {
        $CurrentPageFile.InitialSize = $InitialSize
        $modify = $true
    }
    if ($CurrentPageFile.MaximumSize -ne $MaximumSize)
    {
        $CurrentPageFile.MaximumSize = $MaximumSize
        $modify = $true
    }
    if ($modify)
    {
        $CurrentPageFile.Put()
    }
}
else
{
    # Creates a new page file
    $CurrentPageFile.Delete()
    Set-WmiInstance -Class Win32_PageFileSetting -Arguments @{ Name = $Path; InitialSize = $InitialSize; MaximumSize = $MaximumSize }
}