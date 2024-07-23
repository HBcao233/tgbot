#!/bin/bash
# description: Starts and stops HBcaobot.
# author: HBcao

root=$(dirname $(readlink $0));
bots=();
commands=();

cd ${root};
for i in *; do
  if [ -d "$i" ] && [ -f "$i/.env" ]; then
    commands[${#bots[@]}]="python3 ${root}/main.py $i";
    bots[${#bots[@]}]=$i;
  fi
done

choose() {
  for i in ${!bots[@]}; do
    printf "[%s] %s\n" $i ${bots[$i]};
  done
  printf '请输入序号: '
}

start(){
  if [ -z $1 ]; then
    echo 'Error Args'
    exit 1
  fi
  index=$1
  echo "${bots[$index]} 启动中..."
  nohup python3 ${root}/main.py "${bots[$index]}" > ${root}/${bots[$index]}/bot.log 2>&1 &
}

status(){
  for i in ${!bots[@]}; do
    color=("\E[01m\E[31m" "\E[01m\E[32m");
    statusText=("inactive (dead)" "active (running)");
    status=();
    pid=();
    since=();
    ago=();
    
    k=${commands[$i]};
    echo $k;
    count=`ps -ax | grep "$k" | grep -v grep | grep -v bin | wc -l`;
    if [[ $count -ne 0 ]];then
      status[$i]=1;
      pid[$i]=`ps -ax  | grep "$k" | grep -v grep | awk -F " " 'NR==1{print $1}'`;
      echo ${pid[$i]}
      since[$i]=`ps -o lstart -p ${pid[$i]} | awk 'NR==2'`;
      ago[$i]=`ps -o etime -p ${pid[$i]} | awk 'NR==2{print $1}'`;
    fi
  
    printf "%b●\E[0m $(basename $root)/%s \n" ${color[status[i]]} ${bots[i]};
    printf "%10s: %b%s\E[0m; since %s, %s ago\n" "Active" "${color[status[i]]}" "${statusText[status[i]]}" "${since[i]}" "${ago[i]}"; 
    printf "%10s: %s\n" \
      "PID" "${pid[i]}" \
      "Command" "${commands[i]}";
    printf "\n";
  done
}

stop(){
  if [ -z $1 ]; then
    echo 'Error Args'
    exit 1
  fi
  index=$1
  k=${commands[$index]}
  count=`ps -ax | grep "$k" | grep -v grep | grep -v bin | grep -v sh | wc -l`;
  if [[ $count -ne 0 ]];then
    echo ${bots[$index]}'已启动，正在关闭...';
    ps -ax  | grep "$k" | grep -v grep | grep -v bin | grep -v sh | awk -F " " '{print $1}' | xargs -I {} kill {}
  fi
}


arg1=$1
arg2=$2
case $arg2 in 
start|restart|status|stop|log|cd)
  t=$arg1
  arg1=$arg2
  arg2=$t
  ;;
esac

case $arg1 in
start)
  index=""
  if [ -n $arg2 ]; then
    for i in ${!bots[@]}; do 
      if [ "${bots[$i]}" = "$arg2" ]; then
        index=$i
      fi
    done
  fi
  if [ "$index" = "" ]; then
    if [ ${#bots[@]} = 1 ]; then
      index=0
    else
      choose
      read index
    fi
  fi
  stop $index
  start $index
  ;;
restart)
  if [ ${#bots[@]} = 1 ]; then
    index=0
  else
    choose
    read index
  fi
  stop $index
  start $index
  ;;
stop)
  if [ ${#bots[@]} = 1 ]; then
    index=0
  else
    choose
    read index
  fi
  stop $index
  ;;
status)
  status
  ;;
log)
  index=""
  if [ -n $arg2 ]; then
    for i in ${!bots[@]}; do 
      if [ "${bots[$i]}" = "$arg2" ]; then
        index=$i
        break
      fi
    done
  fi
  if [ "$index" = "" ]; then
    ninput=$arg2
    if [ ${#bots[@]} = 1 ]; then
      index=0
    else
      choose
      read index
    fi
  else
    ninput=$3
  fi
  re='^[0-9]+$'
  num=100
  if [[ $ninput =~ $re ]];then
    num=$arg2
  fi
  echo "查看 ${bots[$index]} 日志"
  nl ${root}/${bots[$index]}/bot.log | tail -n $num
  ;;
cd)
  cd ${root}
  ;;
*)
  echo "Usage: $0 {start|restart|stop|status|log}"
  exit 1
esac
