param(
  [Parameter(Mandatory = $true)]
  [string]$ApiUrl,
  [Parameter(Mandatory = $false)]
  [string]$WebUrl,
  [Parameter(Mandatory = $false)]
  [string]$AppToken,
  [Parameter(Mandatory = $false)]
  [string]$SyncToken
)

$ErrorActionPreference = "Stop"

function Invoke-Json($Method, $Url, $Body = $null, $Headers = @{}) {
  $params = @{
    Method = $Method
    Uri = $Url
    Headers = $Headers
  }
  if ($Body -ne $null) {
    $params.ContentType = "application/json"
    $params.Body = ($Body | ConvertTo-Json -Depth 20)
  }
  Invoke-RestMethod @params
}

$api = $ApiUrl.TrimEnd("/")
$headers = @{}
if ($AppToken) { $headers["X-App-Token"] = $AppToken }
Write-Host "Checking backend status: $api"
$status = Invoke-Json GET "$api/api/status"
if ($status.status -ne "ok") { throw "Backend status is not ok." }
if ($status.database_backend -ne "mongodb") { throw "Production backend is not using MongoDB." }

Write-Host "Checking summary"
$summary = Invoke-Json GET "$api/api/summary" $null $headers
if ($null -eq $summary.latest_health_date) {
  Write-Warning "No health data yet. Run sync before considering production complete."
}

Write-Host "Checking dashboard"
$today = Invoke-Json GET "$api/api/dashboard/today" $null $headers
if ($null -eq $today) { throw "Dashboard response is empty." }

if ($SyncToken) {
  Write-Host "Checking authenticated sync path"
  $syncHeaders = @{}
  if ($AppToken) { $syncHeaders["X-App-Token"] = $AppToken }
  $syncHeaders["X-Sync-Token"] = $SyncToken
  $sync = Invoke-Json POST "$api/api/sync/garmin" @{ days = 7 } $syncHeaders
  if ($sync.status -ne "ok") { throw "Sync did not return ok." }
}

if ($WebUrl) {
  Write-Host "Checking web URL: $WebUrl"
  $web = Invoke-WebRequest -Uri $WebUrl -UseBasicParsing
  if ($web.StatusCode -lt 200 -or $web.StatusCode -ge 400) { throw "Web URL did not return success." }
  if ($web.Content -notmatch "Garmin Insight") { throw "Web page title/content check failed." }
}

Write-Host "Production verification passed."
