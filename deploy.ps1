# Rebuild the recipe bundle, sync the site into the deploy repo, and publish.
param([string]$Message = "Update app")

$ErrorActionPreference = "Stop"
$src    = "C:\Users\mohitdhande\OneDrive - Microsoft\Documents\Microsoft Scout\nutrition-tracker"
$deploy = "C:\Users\mohitdhande\repos\macros"

Write-Host "Rebuilding recipe bundle..."
Push-Location "$src\build"
$env:PYTHONIOENCODING = "utf-8"
python bundle.py
python pantrymatch.py | Select-Object -First 6
Pop-Location

Write-Host "Syncing to $deploy..."
Copy-Item "$src\site\*"          -Destination $deploy -Recurse -Force
Copy-Item "$src\README.md"       -Destination $deploy -Force
Copy-Item "$src\build\*.py"      -Destination "$deploy\build" -Force
Copy-Item "$src\data\recipes.json" -Destination "$deploy\data" -Force

Push-Location $deploy
git add -A
if (git status --porcelain) {
    git -c user.name="Mohit Dhande" -c user.email="mohitdhande@microsoft.com" `
        commit -q -m "$Message

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
    git push -q origin main
    Write-Host "Pushed. Live in about a minute at https://mohit434demo.github.io/macros/"
} else {
    Write-Host "No changes to publish."
}
Pop-Location
