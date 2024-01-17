#!/bin/bash
# chkconfig: 2345 79 80
# description: Starts and stops HBcaobot.
# author: HBcao
# site: https://www.hbcao.top
project="tgbot";
root="/www/wwwroot/"${project};

start(){
    echo '启动中...'
    cd ${root}/ && nohup python3 ${root}/main.py > ${root}/bot.log 2>&1 &
}

status(){
    color=("\E[01m\E[31m" "\E[01m\E[32m");
    status=(0 0);
    statusText=("inactive (dead)" "active (running)");
    pid=(0 0);
    since=("" "");
    ago=("" "");
    command=("python3 ${root}/main.py");

    count=`ps -ax | grep ${project} | grep -v grep | grep -v bin | wc -l`;
    if [[ $count -ne 0 ]];then
      status[i]=1;
      pid[i]=`ps -ax  | grep ${project} | grep -v grep | awk -F " " 'NR==1{print $1}'`;
      since[i]=`ps -o lstart -p ${pid[i]} | awk 'NR==2'`;
      ago[i]=`ps -o etime -p ${pid[i]} | awk 'NR==2{print $1}'`;
    fi

    printf "%b●\E[0m ${project}/%s \n" ${color[status[i]]} ${item[i]};
    printf "%10s: %b%s\E[0m; since %s, %s ago\n" "Active" "${color[status[i]]}" "${statusText[status[i]]}" "${since[i]}" "${ago[i]}"; 
    printf "%10s: %s\n" \
      "PID" "${pid[i]}" \
      "Command" "${command[i]}";
    printf "\n";
    
}

stop(){
    i=${project}/${item[0]}
    count=`ps -ax | grep $i | grep -v grep | grep -v bin | grep -v sh | wc -l`;
    if [[ $count -ne 0 ]];then
        echo $i'已启动，正在关闭...';
        ps -ax  | grep $i | grep -v grep | grep -v bin | grep -v sh | awk -F " " '{print $1}' | xargs -I {} kill {}
    fi
}

set_command(){
  python3 ${root}/set_commands.py
}


case $1 in
start)
  stop
  start
  ;;
restart)
  stop
  start
  ;;
stop)
  stop
  ;;
status)
  status
  ;;
log)
  re='^[0-9]+$'
  if [[ $2 =~ $re ]];then
    nl ${root}/bot.log | tail -n $2
  else
    nl ${root}/bot.log | tail -n 100
  fi
  ;;
set_command)
  set_command
  ;;
set)
  set_command
  ;;
test)
  curl --socks5 127.0.0.1:10808 https://www.pixiv.net
  ;;
cd)
  cd ${root}
  ;;
*)
  echo "Usage: $0 {start|restart|stop|status|golog|botlog|test}"
  exit 1
esac
