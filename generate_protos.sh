tagging() {
	python -m grpc_tools.protoc -I=protos/ \
		--python_out=./libs/media_tagging/media_tagging \
		--grpc_python_out=./libs/media_tagging/media_tagging \
		protos/tagging.proto
}

filonov() {
	python -m grpc_tools.protoc -I=protos/ \
		--python_out=./libs/filonov/filonov \
		--grpc_python_out=./libs/filonov/filonov \
		protos/filonov.proto
}

for i in "$@"; do
  echo "Generating protos " "$i"
  if declare -F "$i" > /dev/null; then
    "$i"
  fi
done
