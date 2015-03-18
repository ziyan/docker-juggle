.PHONY: all
all: build

.PHONY: build
build: docker-juggle-compress docker-juggle-decompress docker-juggle-verify

docker-juggle-compress: cmd/docker-juggle-compress pkg
	@godep go build github.com/ziyan/docker-juggle/cmd/docker-juggle-compress

docker-juggle-decompress: cmd/docker-juggle-decompress pkg
	@godep go build github.com/ziyan/docker-juggle/cmd/docker-juggle-decompress

docker-juggle-verify: cmd/docker-juggle-verify pkg
	@godep go build github.com/ziyan/docker-juggle/cmd/docker-juggle-verify

.PHONY: format
format:
	@gofmt -l -w cmd pkg

.PHONY: save
save:
	@godep save ./...

.PHONY: test
test:
	@godep go test ./...
