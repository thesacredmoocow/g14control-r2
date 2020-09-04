Disable-PnpDevice -InstanceId (Get-PnpDevice -FriendlyName *2060* -Status OK).InstanceId -Confirm:$false

Enable-PnpDevice -InstanceId (Get-PnpDevice -FriendlyName *2060* ).InstanceId -Confirm:$false