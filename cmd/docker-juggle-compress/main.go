package main

import (
	"flag"
	"github.com/golang/glog"
	"os"
	"runtime"
	"archive/tar"
    "io"
)

func main() {

	// use all CPU cores for maximum performance
	runtime.GOMAXPROCS(runtime.NumCPU())

	flag.Parse()

	glog.Warningf("docker-juggle-compress: starting ...")

	tr := tar.NewReader(os.Stdin)
    for {
        hdr, err := tr.Next()
        if err == io.EOF {
            break
        }
        if err != nil {
            break
        }

        glog.Warningf("docker-juggle-compress: %s", hdr.Name)
    }
}
