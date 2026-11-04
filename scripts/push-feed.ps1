# 공고 피드(feed/notices.json)만 하루 한 번 commit/push 한다. 작업 스케줄러 "suitable-home-feed-push" (매일 08:30)
# - notices.json 외 파일은 커밋하지 않는다 (경로 지정 커밋)
# - push 실패 시 pull/merge/force 없이 로그만 남긴다
# - 인증은 git 자격 증명 관리자 사용. 키·토큰을 여기에 쓰지 않는다
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repo
New-Item -ItemType Directory -Force -Path "$repo\local-data" | Out-Null
$log = "$repo\local-data\push-feed.log"
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Add-Content -Encoding utf8 $log }
function Invoke-G { $out = & git.exe @args 2>&1 | ForEach-Object { "$_" }; $code = $LASTEXITCODE; [pscustomobject]@{ Code = $code; Out = ($out -join ' / ') } }

$f = 'feed/notices.json'
if (-not (Test-Path $f)) { Log "파일 없음: $f"; exit 0 }
$st = Invoke-G status --porcelain -- $f
if ($st.Code -ne 0) { Log "git status 실패: $($st.Out)"; exit 1 }
if (-not $st.Out.Trim()) { Log '변화 없음'; exit 0 }

$add = Invoke-G add -- $f
if ($add.Code -ne 0) { Log "git add 실패: $($add.Out)"; exit 1 }
$msg = "chore: 공고 피드 갱신 $(Get-Date -Format 'yyyy-MM-dd')"
$c = Invoke-G commit -m $msg --only -- $f
if ($c.Code -ne 0) { Log "commit 실패: $($c.Out)"; exit 1 }
$p = Invoke-G push origin main
if ($p.Code -ne 0) { Log "push 실패(커밋은 로컬에 있음, 손으로 git pull 후 push): $($p.Out)"; exit 1 }
$h = Invoke-G log -1 --format='%h %s'
Log "push 완료: $($h.Out)"