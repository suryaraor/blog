param(
    [string]$PostDir = "./_posts"
)

$resolvedPostDir = Resolve-Path -Path $PostDir -ErrorAction Stop
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$files = Get-ChildItem -Path $resolvedPostDir -File -Filter "*.md"
$changed = @()

$tokEmDash1 = [string]([char]0x0393) + [char]0x00C7 + [char]0x00F6
$tokEmDash2 = "G" + [char]0x00C7 + [char]0x00F6
$tokApos1 = [string]([char]0x0393) + [char]0x00C7 + [char]0x00D6
$tokApos2 = "G" + [char]0x00C7 + [char]0x00D6
$tokEnDash1 = [string]([char]0x0393) + [char]0x00C7 + [char]0x00F4
$tokEnDash2 = "G" + [char]0x00C7 + [char]0x00F4
$tokLdq = [string]([char]0x0393) + [char]0x00C7 + [char]0x00A3
$tokRdq = [string]([char]0x0393) + [char]0x00C7 + [char]0x00A5
$tokEll = [string]([char]0x0393) + [char]0x00C7 + [char]0x00AA

foreach ($file in $files) {
    $origText = [System.IO.File]::ReadAllText($file.FullName)
    $orig = $origText
    $lineEnding = "`n"

    if ($origText -match "`r`n") {
        $lineEnding = "`r`n"
    }

    $lines = $origText -split "`r?`n", 0
    $outLines = New-Object System.Collections.Generic.List[string]

    foreach ($line in $lines) {
        $nonAsciiCount = ([regex]::Matches($line, "[^\x00-\x7F]")).Count

        if ($nonAsciiCount -ge 10 -and $line -match '^[\s\+\|\-<>"]*$') {
            continue
        }

        $l = $line
        $l = $l.Replace($tokEmDash1, "-")
        $l = $l.Replace($tokEmDash2, "-")
        $l = $l.Replace($tokEnDash1, "-")
        $l = $l.Replace($tokEnDash2, "-")
        $l = $l.Replace($tokApos1, "'")
        $l = $l.Replace($tokApos2, "'")
        $l = $l.Replace($tokLdq, '"')
        $l = $l.Replace($tokRdq, '"')
        $l = $l.Replace($tokEll, "...")

        $l = [regex]::Replace($l, "G[^\x00-\x7F]{2,}", "-")
        $l = [regex]::Replace($l, "[^\x09\x20-\x7E]", "")

        $outLines.Add($l)
    }

    $newText = [string]::Join($lineEnding, $outLines)

    if ($origText.EndsWith("`r`n")) {
        $newText += "`r`n"
    }
    elseif ($origText.EndsWith("`n")) {
        $newText += "`n"
    }

    if ($newText -ne $orig) {
        [System.IO.File]::WriteAllText($file.FullName, $newText, $utf8NoBom)
        $changed += $file.Name
    }
}

"Normalized files: $($changed.Count)"
$changed | Sort-Object
