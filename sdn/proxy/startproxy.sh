DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
java -jar $DIR/proxy.jar --host=0.0.0.0 --port=8082 --debug 2>&1 &
export proxy_pid=$!
sleep 3


when-changed $DIR/phase.data -c "./proxy/setup-starter1.sh"
kill -9 $proxy_pid
