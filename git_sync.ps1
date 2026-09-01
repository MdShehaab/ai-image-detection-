# Git Auto-Sync Helper Script (PowerShell)
# Stages all changes, creates a timestamped commit, and pushes to origin main.

param (
    [string]$Message = "Auto-update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
)

Write-Host "[*] Checking git status..." -ForegroundColor Cyan
git status -s

Write-Host "`n[*] Staging modified and new files..." -ForegroundColor Cyan
git add .

$status = git status --porcelain
if ($status) {
    Write-Host "[*] Committing changes with message: '$Message'..." -ForegroundColor Green
    git commit -m "$Message"

    Write-Host "[*] Pushing to GitHub (origin/main)..." -ForegroundColor Green
    git push origin main
    Write-Host "[+] Successfully synchronized with GitHub!" -ForegroundColor Green
} else {
    Write-Host "[!] No changes detected to commit." -ForegroundColor Yellow
}
