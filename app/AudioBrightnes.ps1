$monitor = Get-WmiObject -ns root/wmi -class wmiMonitorBrightness
$monitor.CurrentBrightness
