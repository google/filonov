tagging() {
	python -m grpc_tools.protoc -I=protos/ \
		--python_out=./libs/media_tagging/media_tagging \
		--grpc_python_out=./libs/media_tagging/media_tagging \
		protos/tagging.proto
}

tagging
