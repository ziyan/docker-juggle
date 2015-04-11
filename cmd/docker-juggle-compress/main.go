package main

import (
	"archive/tar"
	"flag"
	"github.com/golang/glog"
	"github.com/ziyan/docker-juggle/pkg/docker"
	"io"
	"os"
	"runtime"
)

var (
	base = flag.String("base", "511136ea3c5a64f264b78b5433614aec563103b4d4702f3ba7d4d2698e22c158", "base image tag")
)

func main() {

	// use all CPU cores for maximum performance
	runtime.GOMAXPROCS(runtime.NumCPU())

	flag.Parse()

	if err := run(); err != nil {
		glog.Errorf("docker-juggle-compress: %v", err)
		os.Exit(1)
	}
}

func run() error {

	if _, err := docker.History(*base); err != nil {
		return err
	}

	saved, cmd, err := docker.Save(*base)
	if err != nil {
		return err
	}
	defer func() {
		if err := cmd.Wait(); err != nil {
			panic(err)
		}
	}()

	for {
		hdr, err := saved.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		glog.Warningf("docker-juggle-compress: %s", hdr.Name)
	}

	input := tar.NewReader(os.Stdin)
	for {
		hdr, err := input.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		glog.Warningf("docker-juggle-compress: %s", hdr.Name)
	}

	return nil
}
