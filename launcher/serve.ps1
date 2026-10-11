# SIP Compass local launcher (Windows, no install needed).
# Serves the app folder at http://localhost:8765, for this computer only, then opens the browser.
# Read-only: GET/HEAD for app files only. Private folders, the data cache and anything outside the folder are refused.
$ErrorActionPreference = 'Stop'
$port = 8765
$root = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$url  = "http://localhost:$port/SIP-Compass.html"

# Already running? Just open the page.
try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -Method Head -TimeoutSec 2
    if ($r.StatusCode -eq 200) { Start-Process $url; exit 0 }
} catch {}

$types = @{ '.html'='text/html; charset=utf-8'; '.js'='text/javascript; charset=utf-8'; '.json'='application/json; charset=utf-8';
            '.css'='text/css; charset=utf-8'; '.svg'='image/svg+xml'; '.png'='image/png'; '.ico'='image/x-icon'; '.md'='text/plain; charset=utf-8' }
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")
try { $listener.Start() } catch {
    Write-Host "Could not start on port $port (another program may be using it)."
    Write-Host "You can still double-click SIP-Compass.html; only Ask AI needs this launcher."
    Read-Host 'Press Enter to close'; exit 1
}
Write-Host "SIP Compass is open at $url"
Write-Host 'Keep this window open while you use it. Close it to stop.'
Start-Process $url

while ($listener.IsListening) {
    $ctx = $listener.GetContext(); $req = $ctx.Request; $res = $ctx.Response
    try {
        $code = 404
        $hostOk = $req.Headers['Host'] -in @("localhost:$port", "127.0.0.1:$port")
        $rel = [Uri]::UnescapeDataString($req.Url.AbsolutePath).TrimStart('/')
        if ($rel -eq '') { $rel = 'SIP-Compass.html' }
        $full = [IO.Path]::GetFullPath((Join-Path $root $rel))
        $ext = [IO.Path]::GetExtension($full).ToLower()
        $hidden = ($rel -split '[\\/]') | Where-Object { $_.StartsWith('_') -or $_.StartsWith('.') }
        if (-not $hostOk -or $req.HttpMethod -notin @('GET','HEAD')) { $code = 403 }
        elseif ($full.StartsWith($root + [IO.Path]::DirectorySeparatorChar) -and -not $hidden -and $types.ContainsKey($ext) -and (Test-Path -LiteralPath $full -PathType Leaf)) {
            $bytes = [IO.File]::ReadAllBytes($full)
            $res.ContentType = $types[$ext]
            $res.Headers['Cache-Control'] = 'no-store'
            $res.Headers['X-Content-Type-Options'] = 'nosniff'
            $res.ContentLength64 = $bytes.Length
            if ($req.HttpMethod -eq 'GET') { $res.OutputStream.Write($bytes, 0, $bytes.Length) }
            $code = 200
        }
        $res.StatusCode = $code
    } catch { $res.StatusCode = 500 } finally { $res.Close() }
}
