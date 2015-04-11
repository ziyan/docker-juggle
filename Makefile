.PHONY: all
all: build

.PHONY: build
build: docker-juggle-compress docker-juggle-decompress docker-juggle-verify

docker-juggle-compress: $(shell find cmd/docker-juggle-compress 2>/dev/null) $(shell find pkg 2>/dev/null)
	godep go build github.com/ziyan/docker-juggle/cmd/docker-juggle-compress

docker-juggle-decompress: $(shell find cmd/docker-juggle-decompress) $(shell find pkg 2>/dev/null)
	godep go build github.com/ziyan/docker-juggle/cmd/docker-juggle-decompress

docker-juggle-verify: $(shell find cmd/docker-juggle-verify) $(shell find pkg 2>/dev/null)
	godep go build github.com/ziyan/docker-juggle/cmd/docker-juggle-verify

.PHONY: format
format:
	gofmt -l -w cmd pkg

.PHONY: save
save:
	godep save ./...

.PHONY: test
test:
	godep go test ./...
