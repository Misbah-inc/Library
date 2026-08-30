<#
    Fix-LibrarySeo.ps1

    One-time corrections to the published Misbah Library pages:

      1. Absolute, reciprocal, self-referential hreflang on every page.
         Google discards relative hreflang, and ignores a cluster whose members
         do not all point at each other. Arabic previously pointed at nothing,
         so the whole set was being thrown away.

      2. data-alt-<lang> on #page-meta, so the language buttons navigate to the
         real translated URL instead of swapping text in place.

      3. The pager's stale "last" button, which still points at page 84 on the
         older Farsi and Urdu pages, repointed to the real final page.

    Safe to run more than once: every edit is idempotent, so a second run
    reports 0 changed. Reads and writes UTF-8 without a BOM, so Arabic, Urdu
    and Farsi text is preserved exactly.

    Written for Windows PowerShell 5.1.
#>

param(
    [string]$Root = "G:\My Drive\Misbah Library\Library",
    [int]$Last = 231                     # final page of volume 1
)

$Site = "https://library.misbah-inc.com"
$Langs = @("ar", "en", "fa", "ur")

if (-not (Test-Path -LiteralPath (Join-Path $Root "index.html"))) {
    Write-Error "That does not look like the Library root: $Root"
    exit 1
}

$enc = New-Object System.Text.UTF8Encoding($false)
$reAlt = New-Object System.Text.RegularExpressions.Regex '<link rel="alternate" hreflang="[a-z-]+" href="[^"]*">'
$reCanon = New-Object System.Text.RegularExpressions.Regex '(<link rel="canonical" href="[^"]*">)'
$reAltAttr = New-Object System.Text.RegularExpressions.Regex '\s*data-alt-[a-z]+="[^"]*"'
$reMeta = New-Object System.Text.RegularExpressions.Regex '(<div id="page-meta" hidden)\s*'
$rePath = New-Object System.Text.RegularExpressions.Regex '^(?:(en|fa|ur)/)?bihar/(\d+)/(\d+)/index\.html$'

$changed = 0
$seen = 0

Get-ChildItem -LiteralPath $Root -Recurse -Filter index.html | ForEach-Object {
    $full = $_.FullName
    # normalise separators so the path test behaves the same everywhere;
    # $full is still used verbatim for the actual read and write
    $rel = $full.Substring($Root.Length).TrimStart('\', '/').Replace('\', '/')

    $m = $rePath.Match($rel)
    if (-not $m.Success) { return }          # section pages carry no canonical

    $lang = $m.Groups[1].Value
    if ([string]::IsNullOrEmpty($lang)) { $lang = "ar" }
    $vol = $m.Groups[2].Value
    $n = $m.Groups[3].Value
    $seen++

    if ($lang -eq "ar") { $depth = "../../.." } else { $depth = "../../../.." }

    $text = [System.IO.File]::ReadAllText($full, [System.Text.Encoding]::UTF8)
    $orig = $text

    # ---- 1. absolute reciprocal hreflang -------------------------------------
    $block = ""
    foreach ($a in $Langs) {
        if ($a -eq "ar") { $pre = "" } else { $pre = "/$a" }
        $block += '<link rel="alternate" hreflang="' + $a + '" href="' + $Site + $pre + '/bihar/' + $vol + '/' + $n + '/">'
    }
    $block += '<link rel="alternate" hreflang="x-default" href="' + $Site + '/bihar/' + $vol + '/' + $n + '/">'

    $text = $reAlt.Replace($text, "")
    $text = $reCanon.Replace($text, ('$1' + $block), 1)

    # ---- 2. data-alt-* on #page-meta ----------------------------------------
    $attrs = @()
    foreach ($a in $Langs) {
        if ($a -eq $lang) { continue }
        if ($a -eq "ar") { $pre = "" } else { $pre = "/$a" }
        $attrs += 'data-alt-' + $a + '="' + $depth + $pre + '/bihar/' + $vol + '/' + $n + '/"'
    }
    $joined = [string]::Join(" ", $attrs)
    $text = $reAltAttr.Replace($text, "")
    $text = $reMeta.Replace($text, ('$1 ' + $joined + ' '), 1)

    # ---- 3. stale "last" button ---------------------------------------------
    if ($lang -eq "ar") { $lastPrefix = '\.\./\.\./\.\./bihar/' } else { $lastPrefix = '\.\./\.\./\.\./\.\./' + $lang + '/bihar/' }
    $reLast = New-Object System.Text.RegularExpressions.Regex ('(href="' + $lastPrefix + $vol + '/)\d+(/" rel="related"><span data-i18n="last">)')
    $text = $reLast.Replace($text, ('${1}' + $Last + '$2'))

    if ($text -ne $orig) {
        [System.IO.File]::WriteAllText($full, $text, $enc)
        $changed++
    }
}

Write-Host ""
Write-Host "pages examined : $seen"
Write-Host "pages changed  : $changed"
Write-Host ""
Write-Host "Run it again and 'pages changed' should be 0."
