package main

import (
	"flag"
	"github.com/golang/glog"
	"runtime"
)

func main() {

	// use all CPU cores for maximum performance
	runtime.GOMAXPROCS(runtime.NumCPU())

	flag.Parse()

	glog.Warningf("docker-juggle-decompress: starting ...")
}
