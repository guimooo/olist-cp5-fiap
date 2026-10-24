<#
Executa consultas DAX (ou comandos TMSL) contra o modelo aberto no Power BI Desktop.

Uso:
  powershell -File executar_dax.ps1 -Arquivo consultas.dax [-Saida resultado.txt]
  powershell -File executar_dax.ps1 -Tmsl comando.json
O arquivo .dax pode ter várias consultas separadas por uma linha "-- ##". Cada resultado é
impresso como tabela de texto, precedido do nome da consulta (primeira linha "-- nome").
#>
param([string]$Arquivo, [string]$Tmsl, [string]$Saida)

$pbi = (Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop).InstallLocation
if (-not $pbi) { $pbi = "C:\Program Files\Microsoft Power BI Desktop" }
Add-Type -Path (Join-Path $pbi "bin\Microsoft.PowerBI.AdomdClient.dll")

# Porta da instância local do Analysis Services aberta pelo Desktop
$pid_as = (Get-Process msmdsrv -ErrorAction Stop | Select-Object -First 1).Id
$porta = (Get-NetTCPConnection -OwningProcess $pid_as -State Listen | Where-Object LocalAddress -in '127.0.0.1', '::1' |
          Select-Object -First 1).LocalPort
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection "Data Source=localhost:$porta"
$conn.Open()
$c0 = $conn.CreateCommand()
$c0.CommandText = 'SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS'
$r0 = $c0.ExecuteReader(); [void]$r0.Read(); $db = $r0.GetValue(0); $r0.Close()
$conn.ChangeDatabase($db)

$out = New-Object System.Text.StringBuilder
[void]$out.AppendLine("servidor localhost:$porta  banco $db")

if ($Tmsl) {
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = (Get-Content $Tmsl -Raw -Encoding UTF8).Replace('{DB}', $db)
    $cmd.CommandTimeout = 600
    [void]$cmd.ExecuteNonQuery()
    [void]$out.AppendLine("TMSL executado")
}

if ($Arquivo) {
    $texto = Get-Content $Arquivo -Raw -Encoding UTF8
    foreach ($bloco in ($texto -split "(?m)^-- ##\s*$")) {
        $bloco = $bloco.Trim()
        if (-not $bloco) { continue }
        $nome = ($bloco -split "`n")[0].Trim()
        [void]$out.AppendLine("`n### $nome")
        try {
            $cmd = $conn.CreateCommand()
            $cmd.CommandText = $bloco
            $r = $cmd.ExecuteReader()
            $cols = @(); for ($i = 0; $i -lt $r.FieldCount; $i++) { $cols += $r.GetName($i) }
            [void]$out.AppendLine(($cols -join " | "))
            while ($r.Read()) {
                $vals = @(); for ($i = 0; $i -lt $r.FieldCount; $i++) {
                    $v = $r.GetValue($i)
                    if ($v -is [double]) { $v = $v.ToString("0.######", [Globalization.CultureInfo]::InvariantCulture) }
                    if ($null -eq $v -or $v -is [DBNull]) { $v = "(vazio)" }
                    $vals += "$v"
                }
                [void]$out.AppendLine(($vals -join " | "))
            }
            $r.Close()
        } catch {
            [void]$out.AppendLine("ERRO: $($_.Exception.Message)")
        }
    }
}
$conn.Close()
if ($Saida) { [IO.File]::WriteAllText($Saida, $out.ToString(), (New-Object Text.UTF8Encoding $false)) }
$out.ToString()
