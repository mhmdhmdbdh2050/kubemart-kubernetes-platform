$ErrorActionPreference = 'Stop'

$sourcePath = Join-Path $PSScriptRoot 'KubeMart-DevOps-Guide-Arabic.html'
$pdfPath = Join-Path $PSScriptRoot 'KubeMart-DevOps-Guide-Arabic.pdf'
$svgPath = Join-Path $PSScriptRoot 'KubeMart-Architecture-Arabic.svg'

if (-not (Test-Path -LiteralPath $sourcePath)) {
    throw "HTML source not found: $sourcePath"
}

# Keep the standalone vector diagram synchronized with the embedded source.
$html = Get-Content -LiteralPath $sourcePath -Raw
$svgMatch = [regex]::Match($html, '<svg[\s\S]*?</svg>')
if (-not $svgMatch.Success) {
    throw 'Architecture SVG was not found in the HTML source.'
}
[System.IO.File]::WriteAllText($svgPath, $svgMatch.Value, [System.Text.UTF8Encoding]::new($false))

$browserCandidates = @(
    'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
)
$browser = $browserCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $browser) {
    throw 'Install Google Chrome or Microsoft Edge to print the Arabic HTML source to PDF.'
}

$profilePath = Join-Path ([System.IO.Path]::GetTempPath()) ("kubemart-pdf-" + [guid]::NewGuid().ToString())
$tempPdfPath = Join-Path $PSScriptRoot 'KubeMart-DevOps-Guide-Arabic.tmp.pdf'
$htmlUri = ([System.Uri]$sourcePath).AbsoluteUri
$arguments = @(
    '--headless', '--disable-gpu', '--disable-software-rasterizer',
    '--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader',
    '--disable-features=Vulkan,UseSkiaRenderer',
    "--user-data-dir=`"$profilePath`"",
    '--no-pdf-header-footer',
    "--print-to-pdf=`"$tempPdfPath`"",
    "`"$htmlUri`""
)

try {
    $process = Start-Process -FilePath $browser -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $tempPdfPath)) {
        throw "Browser PDF generation failed with exit code $($process.ExitCode)."
    }
    Move-Item -LiteralPath $tempPdfPath -Destination $pdfPath -Force
    Write-Output "Created $pdfPath"
}
finally {
    if (Test-Path -LiteralPath $tempPdfPath) {
        Remove-Item -LiteralPath $tempPdfPath -Force
    }
    if (Test-Path -LiteralPath $profilePath) {
        Remove-Item -LiteralPath $profilePath -Recurse -Force
    }
}
