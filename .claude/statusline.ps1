[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {
    $inputText = [Console]::In.ReadToEnd()
    $j = $inputText | ConvertFrom-Json -ErrorAction Stop
    $m = $j.model.display_name
    $d = Split-Path $j.workspace.current_dir -Leaf
    $b = ''
    try {
        $g = git branch --show-current 2>$null
        if ($g) { $b = " | $g" }
    } catch {}
    Write-Host "[$m] $d$b"
} catch {
    Write-Host "[Claude] blog-post"
}
