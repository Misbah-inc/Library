<#
    Set-AssetVersion.ps1

    Stamps a version marker onto every reference to reader.css and reader.js:

        assets/reader.js          ->  assets/reader.js?v=3
        assets/reader.js?v=2      ->  assets/reader.js?v=3

    Why this exists: browsers cache those two files hard, and GitHub Pages
    does nothing to stop them. A returning visitor keeps yesterday's script
    against today's markup, which shows up as untranslated labels and controls
    that do nothing — the bug looks like a mobile bug but is a cache.

    Run this whenever reader.css or reader.js changes, with the version bumped.
    Idempotent: a second run at the same version reports 0 changed.

    Written for Windows PowerShell 5.1.
#>

param(
    [string]$Root = "G:\My Drive\Misbah Library\Library",
    [int]$Version = 3
)

if (-not (Test-Path -LiteralPath (Join-Path $Root "index.html"))) {
    Write-Error "That does not look like the Library root: $Root"
    exit 1
}

$enc = New-Object System.Text.UTF8Encoding($false)
$re = New-Object System.Text.RegularExpressions.Regex 'assets/reader\.(css|js)(\?v=\d+)?'

$changed = 0
$seen = 0

Get-ChildItem -LiteralPath $Root -Recurse -Filter *.html | ForEach-Object {
    $full = $_.FullName
    $text = [System.IO.File]::ReadAllText($full, [System.Text.Encoding]::UTF8)
    if ($text -notmatch 'assets/reader\.') { return }
    $seen++

    $new = $re.Replace($text, ('assets/reader.$1?v=' + $Version))
    if ($new -ne $text) {
        [System.IO.File]::WriteAllText($full, $new, $enc)
        $changed++
    }
}

Write-Host ""
Write-Host "pages referencing the assets : $seen"
Write-Host "pages updated to v=$Version   : $changed"
Write-Host ""
Write-Host "Run again and 'pages updated' should be 0."
