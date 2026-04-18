param(
    [string]$PostsDir = "./_posts",
    [string]$UnlistedDir = "./_unlisted",
    [string[]]$Keywords = @(
        "political",
        "politics",
        "regulation",
        "government",
        "policy",
        "election",
        "layoff",
        "inequality",
        "wealth gap",
        "economic divide",
        "antitrust",
        "pentagon",
        "carbon",
        "climate",
        "water",
        "controversial",
        "controversy",
        "controversies",
        "uncomfortable truth"
    ),
    [switch]$WhatIf
)

$resolvedPostsDir = Resolve-Path -Path $PostsDir -ErrorAction Stop
if (-not (Test-Path -Path $UnlistedDir)) {
    New-Item -ItemType Directory -Path $UnlistedDir -Force | Out-Null
}
$resolvedUnlistedDir = Resolve-Path -Path $UnlistedDir -ErrorAction Stop

$files = Get-ChildItem -Path $resolvedPostsDir -File -Filter "*.md" | Sort-Object Name
$moved = New-Object System.Collections.Generic.List[string]
$matched = New-Object System.Collections.Generic.List[string]

foreach ($file in $files) {
    $content = [System.IO.File]::ReadAllText($file.FullName)
    $lower = $content.ToLowerInvariant()

    $isExplicitUnlisted = $lower -match "(?m)^unlisted:\s*true\s*$"
    $hit = $null

    if (-not $isExplicitUnlisted) {
        foreach ($keyword in $Keywords) {
            $escaped = [regex]::Escape($keyword.ToLowerInvariant()).Replace("\ ", "\\s+")
            $pattern = "\\b$escaped\\b"

            if ([regex]::IsMatch($lower, $pattern)) {
                $hit = $keyword
                break
            }
        }
    }

    if ($isExplicitUnlisted -or $hit) {
        $destination = Join-Path $resolvedUnlistedDir $file.Name
        $reason = if ($isExplicitUnlisted) { "front matter unlisted:true" } else { "keyword: $hit" }

        if ($WhatIf) {
            "Would move {0} ({1})" -f $file.Name, $reason
        }
        else {
            Move-Item -Path $file.FullName -Destination $destination -Force
            "Moved {0} ({1})" -f $file.Name, $reason
            $moved.Add($file.Name) | Out-Null
            $matched.Add("{0} => {1}" -f $file.Name, $reason) | Out-Null
        }
    }
}

if ($WhatIf) {
    "Dry run complete."
}
else {
    "Moved files: $($moved.Count)"
    $matched | Sort-Object
}
