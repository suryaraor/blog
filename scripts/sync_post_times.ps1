param(
    [string]$PostDir = "./_posts"
)

$resolvedPostDir = Resolve-Path -Path $PostDir -ErrorAction Stop
$files = Get-ChildItem -Path $resolvedPostDir -File -Filter "*.md"
$updated = @()

$groups = $files | Group-Object {
    if ($_.BaseName -match '^(\d{4}-\d{2}-\d{2})-') {
        $matches[1]
    } else {
        ""
    }
}

foreach ($group in $groups) {
    if ([string]::IsNullOrWhiteSpace($group.Name)) {
        continue
    }

    # Oldest edited gets lowest time; newest edited gets highest time.
    $ordered = $group.Group | Sort-Object LastWriteTime, Name
    $counter = 1

    foreach ($file in $ordered) {
        $newDate = "{0} {1}" -f $group.Name, ([TimeSpan]::FromSeconds($counter).ToString('hh\:mm\:ss'))
        $content = Get-Content -Path $file.FullName -Raw

        if ($content -notmatch '(?ms)^---\s*\r?\n.*?\r?\n---') {
            $counter++
            continue
        }

        $frontMatter = $matches[0]
        if ($frontMatter -match '(?m)^date:\s*.*$') {
            $newFrontMatter = [regex]::Replace($frontMatter, '(?m)^date:\s*.*$', "date: $newDate")
        } else {
            $newFrontMatter = $frontMatter -replace '\r?\n---$', "`r`ndate: $newDate`r`n---"
        }

        if ($newFrontMatter -ne $frontMatter) {
            $newContent = $content.Substring(0, $frontMatter.Length).Replace($frontMatter, $newFrontMatter) + $content.Substring($frontMatter.Length)
            Set-Content -Path $file.FullName -Value $newContent -NoNewline
            $updated += "{0} => {1}" -f $file.Name, $newDate
        }

        $counter++
    }
}

"Updated files: $($updated.Count)"
$updated | Sort-Object
