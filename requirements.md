Today, lower level patch reports are generated this way:

1. Getting info
All hosts have this on the crontab:

```bash
#Ansible: hostinfo
10 6,12 * * * /home/nocmon/hostinfo.bash > /home/nocmon/$HOSTNAME
#Ansible: cfg2html
19 6,12 * * * /home/nocmon/cfg2html.bash >/dev/null 2>&1
```

/home/nocmon/hostinfo.bash content:

```bash
#! /bin/bash
# for CenOS and RedHat
DATE=$(date +"%Y-%m-%d")
hostname|tr '\n\n' ',';hostname -I | awk '{print$1}'|tr '\n\n' ',';yum history |grep ', U'| head -n 1| awk -F"|" '{print$3}'| awk '{print$1}'|tr '\n' ',';who -b | cut -c23-32| tr '\n' ',';echo $DATE|tr '\n\n' ',';cat /etc/redhat-release|tr '\n\n' ',';uname -r |tr '\n\n' ','; needs-restarting -r |grep 'required\|necessary'
```

The contents of this generated file:
```
# cat spspace02v.uss.net
spspace02v.uss.net,10.41.128.140,2026-06-30,2026-07-25,2026-07-27,Red Hat Enterprise Linux release 8.10 (Ootpa),4.18.0-553.129.1.el8_10.x86_64,Reboot should not be necessary.
```

This is copied from each host to a main server and then processed by a script to generate a report. The report includes the hostname, IP address, last update date, next scheduled update, last reboot date, OS version, kernel version, and whether a reboot is necessary.


The patching reports scripts are (from central server root's crontab):

```
## Patching reports
0 7 * * 1,3,5  /root/patching/reports/patchreport.bash > /root/patching/reports/report.log 2>&1
0 5 1 * * /root/patching/reports/hosts_details_report.bash > /root/patching/reports/report.log 2>&1
30 5 1 * * /root/patching/reports/patchreport_oracle.bash  > /root/patching/reports/report.log 2>&1
0 2 * * 1,3,4,5 /root/patching/reports/patchreportSBox.bash /root/patching/reports/report.SB.log 2>&1
```

/root/patching/reports/patchreport.bash content:

```bash
cat /root/patching/reports/patchreport.bash

#!/bin/bash
# Create Report
# Send Report via Email.
# succsess = tested
# Ahmer Aziz
# V 1.2
# Pre updated 02/22/2021
# last updated 02/22/2021

DATE=$(date +"%m%d%Y")

## For Lower Level

echo -e "This is auto generated report. \nPatch report for Lower level all online servers. \nDate = $DATE "> /root/patching/reports/patch_repo_LWR.txt
echo -e "Hostname, Host IP, Patched Date, Last reboot, Date reported, OS Release, Current Kernel, Remarks for Reboot " > /root/patching/reports/Patch_Report_LWR.csv

grep 10.44 /inventory/* |  grep Reboot |awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_LWR.csv
grep 10.42 /inventory/* |  grep Reboot| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_LWR.csv
grep 10.44 /inventory/* |  grep -v Reboot |awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_LWR.csv
grep 10.42 /inventory/* |  grep -v Reboot| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_LWR.csv


#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_LWR.csv -s "Patch report for Lower level all online servers  $DATE" lpatel@InComm.com -c  uxteam@incomm.com < /root/patching/reports/patch_repo_LWR.txt > /dev/null
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_LWR.csv -s "Patch report for Lower level all online servers  $DATE" aaziz@InComm.com  < /root/patching/reports/patch_repo_LWR.txt  > /dev/null
## With BCC
mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_LWR.csv -s "Patch report for Lower level all online servers $DATE" lpatel@InComm.com -c  uxteam@incomm.com wlorca@incomm.com jzabek@incomm.com < /root/patching/reports/patch_repo_LWR.txt> /dev/null

## Mail to me only
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_LWR.csv -s "Patch report for Lower level all online servers  $DATE" aaziz@InComm.com  < /root/patching/reports/patch_repo_LWR.txt > /dev/null


## For Production CAT3

echo -e "This is auto generated report. \nPatch report for Production CAT3 all online servers.. \nDate = $DATE "> /root/patching/reports/patch_Report_CAT3.txt
echo -e "Hostname, Host IP, Patched Date, Last reboot, Date reported, OS Release, Current Kernel, Remarks for Reboot " > /root/patching/reports/Patch_Report_CAT3.csv

grep 10.40. /inventory/* |  grep Reboot| grep -v 10.40.98| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_CAT3.csv
grep 10.140. /inventory/* |  grep Reboot | awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_CAT3.csv
grep 10.190. /inventory/* |  grep Reboot| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_CAT3.csv
grep 10.40. /inventory/* |  grep -v Reboot| grep -v 10.40.98| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_CAT3.csv
grep 10.140. /inventory/* |  grep -v Reboot | awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_CAT3.csv
grep 10.190. /inventory/* |  grep -v Reboot| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_CAT3.csv
grep 10.83. /inventory/* |  grep -v Reboot| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_CAT3.csv
grep 10.82. /inventory/* |  grep -v Reboot| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_CAT3.csv



#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_CAT3.csv -s "Patch report for Production CAT3 all online servers  $DATE" lpatel@InComm.com -c  uxteam@incomm.com < /root/patching/reports/patch_Report_CAT3.txt > /dev/null
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_CAT3.csv -s "Patch report for Production CAT3 all online servers  $DATE" aaziz@InComm.com  < /root/patching/reports/patch_Report_CAT3.txt > /dev/null
## With BCC
mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_CAT3.csv -s "Patch report for Production CAT3 all online servers  $DATE" lpatel@InComm.com -c  uxteam@incomm.com wlorca@incomm.com jzabek@incomm.com < /root/patching/reports/patch_Report_CAT3.txt  > /dev/null

## Mail to me only
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_CAT3.csv -s "Patch report for Production CAT3 all online servers  $DATE" aaziz@InComm.com  < /root/patching/reports/patch_Report_CAT3.txt > /dev/null





## FCV_ DMZ PART
echo -e "This is auto generated report. \nPatch report for FCV DMZ All server. \nDate = $DATE "> /root/patching/reports/patch_Report_FCV_DMZ.txt

echo -e "Hostname, Host IP, Patched Date, Last reboot, Date reported, OS Release, Current Kernel, Remarks for Reboot " > /root/patching/reports/Patch_FCV_DMZ_Report.csv

grep 10.41. /inventory/* |  grep Reboot | awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.40.98. /inventory/* |  grep Reboot | awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.40.99. /inventory/* |  grep Reboot | awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.141. /inventory/*  |  grep Reboot | awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.191. /inventory/* |  grep Reboot | awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.41. /inventory/* |  grep Reboot -v| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.40.98. /inventory/* |  grep Reboot -v| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.40.99. /inventory/* |  grep Reboot -v| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.141. /inventory/*  |  grep Reboot -v| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.191. /inventory/* |  grep Reboot -v| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv
grep 10.86. /inventory/*|  grep Reboot -v| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_FCV_DMZ_Report.csv

#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_FCV_DMZ_Report.csv -s "Patch report for Production CAT1 and DMZ all online servers $DATE" lpatel@InComm.com -c  uxteam@incomm.com jzabek@incomm.com wlorca@incomm.com < /root/patching/reports/patch_Report_FCV_DMZ.txt > /dev/null
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_FCV_DMZ_Report.csv -s "Patch report for Production CAT1 and DMZ all online servers $DATE" lpatel@InComm.com -c  uxteam@incomm.com < /root/patching/reports/patch_Report_FCV_DMZ.txt /dev/null
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_FCV_DMZ_Report.csv -s "Patch report for Production CAT1 and DMZ all online servers $DATE" aaziz@InComm.com  < /root/patching/reports/patch_Report_FCV_DMZ.txt > /dev/null
## With BCC
mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_FCV_DMZ_Report.csv -s "Patch report for Production CAT1 and DMZ all online servers $DATE" lpatel@InComm.com -c  uxteam@incomm.com wlorca@incomm.com jzabek@incomm.com < /root/patching/reports/patch_Report_FCV_DMZ.txt > /dev/null

## Mail to me only
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_FCV_DMZ_Report.csv -s "Patch report for Production CAT1 and DMZ all online servers  $DATE" aaziz@InComm.com  < /root/patching/reports/patch_Report_FCV_DMZ.txt > /dev/null

## For servers have some issues.

echo -e "This is auto generated report. \nReport for servers not reporting or have some issues. \nDate = $DATE "> /root/patching/reports/Report_bad_servers.txt
echo -e "Host name/Host IP " > /root/patching/reports/Report_isssues_servers.txt
for i in `ls -l /inventory/  | grep "nocmon   0" | awk '{print$9}'`;do nslookup $i  | grep -v 127.0 | grep -v Non-authoritative; done >> /root/patching/reports/Report_isssues_servers.txt


mailx -r uxteam@incomm.com -a /root/patching/reports/Report_isssues_servers.txt -s "Report for servers not reporting or have some issues.  $DATE"  uxteam@incomm.com < /root/patching/reports/Report_bad_servers.txt  > /dev/null
## Mail to me only
#mailx -r uxteam@incomm.com -a /root/patching/reports/Report_isssues_servers.txt -s "Report for servers not reporting or have some issues.  $DATE" aaziz@InComm.com  < /root/patching/reports/Report_bad_servers.txt > /dev/null



#OLS ALL Prd and SandBox

#echo -e "This is auto generated report. \nPatch report for OLS Dallas and Plano online servers. \nDate = $DATE "> /root/patching/reports/patch_repo_OLS.txt
#echo -e "Hostname, Host IP, Patched Date, Last reboot, Date reported, OS Release, Current Kernel, Remarks for Reboot " > /root/patching/reports/Patch_Report_OLS.csv

#grep 10.116 /inventory/* |  grep Reboot |awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_OLS.csv
#grep 10.116 /inventory/* |  grep Reboot| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_OLS.csv
#grep 10.117 /inventory/* |  grep -v Reboot |awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_OLS.csv
#grep 10.117 /inventory/* |  grep -v Reboot| awk -F ":" '{print $2}' >> /root/patching/reports/Patch_Report_OLS.csv


#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_OLS.csv -s "Patch report for Lower level all online servers  $DATE" lpatel@InComm.com -c  uxteam@incomm.com < /root/patching/reports/patch_repo_OLS.txt > /dev/null
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_OLS.csv -s "Patch report for Lower level all online servers  $DATE" aaziz@InComm.com  < /root/patching/reports/patch_repo_OLS.txt  > /dev/null
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_OLS.csv -s "Patch report for Lower level all online servers  $DATE"  aaziz@InComm.com -c  uxteam@incomm.com < /root/patching/reports/patch_repo_OLS.txt > /dev/null
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_OLS.csv -s "Patch report for OLS servers  $DATE"  uxteam@incomm.com < /root/patching/reports/patch_repo_OLS.txt > /dev/null

## With BCC
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_OLS.csv -s "Patch report for Lower level all online servers $DATE" lpatel@InComm.com -c  uxteam@incomm.com wlorca@incomm.com jzabek@incomm.com < /root/patching/reports/patch_repo_OLS.txt> /dev/null


#END
```

/root/patching/reports/hosts_details_report.bash content:

```bash
cat /root/patching/reports/hosts_details_report.bash
#!/bin/bash
# script for monthly report Hosts details
# Ahmer Aziz
# V 1.0
# 03/01/2021

DATE=$(date +"%m%d%Y")

## Genrated monthly report for hosts not reporting more than a month /offline_4month
echo -e "This is auto genrated monthly report. \n Monthly Hosts details report for offline servers for more than month and decommissioned servers list. \nDate = $DATE "> /root/patching/reports/Hosts_details_report.txt
echo -e "Hostname, Host IP" > /root/patching/reports/server_offline_for_month.csv
/bin/find  /inventory/* -maxdepth 1 -mtime +30 -exec mv '{}' /offline_4month/ ';' > /dev/null
grep 10  /offline_4month/* | awk -F ":" '{print $2}' | awk -F "," '{print $1","$2}'>> server_offline_for_month.csv


# Hosts not reporting more than two months or may be Decommissioned offline_Decomm/
echo -e "Hostname, Host IP" > /root/patching/reports/Hosts_Decommissioned_report.csv
/bin/find  /offline_4month/* -maxdepth 1 -mtime +60 -exec mv '{}' /offline_Decomm/ ';' > /dev/null
grep 10  /offline_Decomm/* | awk -F ":" '{print $2}' | awk -F "," '{print $1","$2}'>> Hosts_Decommissioned_report.csv

mailx -r uxteam@incomm.com -a /root/patching/reports/Hosts_Decommissioned_report.csv -a /root/patching/reports/server_offline_for_month.csv -s "Monthly report for hosts Status $DATE" uxteam@incomm.com < /root/patching/reports/Hosts_details_report.txt > /dev/nul
#END
```

/root/patching/reports/patchreport_oracle.bash content:

```bash
cat /root/patching/reports/patchreport_oracle.bash
#!/bin/bash
# Create Report
# Send Report via Email.
# succsess = tested
# Ahmer Aziz
# V 1.2
# Pre updated 02/22/2021
# last updated 05/06/2021

DATE=$(date +"%m%d%Y")

## For all Oracle DBA team (OracleDBATeam <OracleDBATeam@incomm.com> )not include FIN servers.

echo -e "This is auto genrated report. \nPatch report for Oracle servers only OracleDBA servers. \nDate = $DATE "> /root/patching/reports/patch_repo_oracle.txt
echo -e "Hostname, Host IP, Patched Date, Last reboot, Date reported, OS Release, Current Kernel, Remarks for Reboot " > /root/patching/reports/Patch_Report_oracle.csv

grep odb /inventory/* | awk -F ":" '{print $2}'| sort  >> /root/patching/reports/Patch_Report_oracle.csv
grep ora /inventory/* | grep -v fin | awk -F ":" '{print $2}'| sort  >> /root/patching/reports/Patch_Report_oracle.csv

## With BCC
mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_oracle.csv -s "Patch report for Oracle servers only OracleDBA servers  $DATE" OracleDBATeam@incomm.com -c  uxteam@incomm.com  < /root/patching/reports/patch_repo_oracle.txt > /dev/nul

## Mail to me only
mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_Report_oracle.csv -s "Patch report for Oracle servers only OracleDBA servers   $DATE" aaziz@InComm.com  < /root/patching/reports/patch_repo_oracle.txt > /dev/nul

#END
```


/root/patching/reports/patchreportSBox.bash content:

```bash
cat /root/patching/reports/patchreportSBox.bash
#!/bin/bash
# Create Report
# file = /root/patching/reports/patchreportSBox.bash
# crontab = 0 2 * * 1,3,4,5 /root/patching/reports/patchreportSBox.bash /root/patching/reports/report.SB.log 2>&1
# Send Report via Email.
# succsess = tested
# Ahmer Aziz
# V 2.0
# Pre updated 01/18/2019
# last updated 04/22/2021

DATE=$(date +"%m%d%Y")

## SBox patch report
echo -e "This is auto genrated report. \nPatch report for Sand Box servers. \nDate = $DATE "> /root/patching/reports/repo_Sbox.txt

echo -e "Hostname, Host IP, Patched Date, Last reboot, Date reported, OS Release, Current Kernel, Remarks for Reboot " > /root/patching/reports/Patch_SBox_Report.csv
grep 10.42.32.46 /inventory/* | awk -F ":" '{print$2}' >> /root/patching/reports/Patch_SBox_Report.csv
grep 10.42.32.55 /inventory/* | awk -F ":" '{print$2}' >> /root/patching/reports/Patch_SBox_Report.csv
grep 10.114.9.33 /home/ansible/inventory/* | awk -F ":" '{print$2}' >> /root/patching/reports/Patch_SBox_Report.csv
grep 10.114.9.35 /home/ansible/inventory/* | awk -F ":" '{print$2}' >> /root/patching/reports/Patch_SBox_Report.csv
grep 10.42.32.45 /inventory/* | awk -F ":" '{print$2}' >> /root/patching/reports/Patch_SBox_Report.csv

# Mail to destro
mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_SBox_Report.csv -s "Patch report Sand Box servers $DATE " lpatel@InComm.com -c  uxteam@incomm.com jzabek@incomm.com wlorca@incomm.com < /root/patching/reports/repo_Sbox.txt > /dev/nul

# only me
#mailx -r uxteam@incomm.com -a /root/patching/reports/Patch_SBox_Report.csv -s "Patch report Sand Box servers $DATE " aaziz@InComm.com < /root/patching/reports/repo_Sbox.txt > /dev/nul

#END
```


Finally, on each server, the `nocmon` user runs a script that scp the local files to the main server. The main server then runs the above scripts to generate the reports and send them via email.

Example on a client that runs the script:
```bash
su - nocmon
Last login: Wed Jan 29 17:58:39 EST 2025

[nocmon@sslsplsh03v ~]$ crontab -l
MAILTO =
#Ansible: cfg2html_scp
6 6,12 * * * /home/nocmon/cfg2html_scp.bash >/dev/null 2>&1

cat /home/nocmon/cfg2html_scp.bash
#! /bin/bash
#/usr/bin/scp -oStrictHostKeyChecking=no "/etc/cfg2html/`hostname`.html" 10.41.128.140:/cfg2html/
/usr/bin/scp -oStrictHostKeyChecking=no "/home/nocmon/$HOSTNAME" 10.41.128.140:/inventory
```


Based on all this info, I want now:

I want to renew this solution. Starting with the LLE hosts.

So, The patching report should include the following information for each server:

Hostname
IP Address
Patch Date
Last Reboot Date/Time
Operating System Release

## Inventory sources

### Location: Spacewalk - spspace02v
/backup/patching/monthly/LWR/QTS_RHEL_LWR.ini 
/backup/patching/monthly/LWR/OLS_ATL_LWR.ini  
/backup/patching/monthly/LWR/OLS_QTS_LWR.ini

### Oracle servers
/backup/patching/monthly/LWR/QTS_OEL_LWR.ini

Reporting Requirements
  Primary Report
  Generate a consolidated patch status report containing:

  Hostname
  IP Address
  Patch Date
  Last Reboot Date
  OS Release
  Patch Status

Secondary Report
  Generate a separate report for:

  Unreachable servers
  Servers with connection failures
  Servers that could not be assessed during report generation

I want a nice format, not a simple csv file. I want it to be readable and well-structured, possibly in HTML or PDF format. The report should have a clear header, sections for each server, and use tables to present the data. This will be presented to higher management, so it should be professional and visually appealing.

