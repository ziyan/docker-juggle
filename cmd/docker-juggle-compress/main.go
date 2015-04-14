package main

import (
	"archive/tar"
	"bytes"
	"crypto/sha1"
	"encoding/base64"
	"encoding/hex"
	"flag"
	"github.com/golang/glog"
	"github.com/ziyan/docker-juggle/pkg/docker"
	"io"
	"os"
	"runtime"
	"strconv"
	"strings"
)

var (
	base = flag.String("base", "511136ea3c5a64f264b78b5433614aec563103b4d4702f3ba7d4d2698e22c158", "base image tag")
)

func main() {

	// use all CPU cores for maximum performance
	runtime.GOMAXPROCS(runtime.NumCPU())

	flag.Parse()

	if err := run(); err != nil {
		glog.Exitf("docker-juggle-compress: %v", err)
	}
}

func run() error {

	history, index, err := prepare(*base)
	if err != nil {
		return err
	}

	input := tar.NewReader(os.Stdin)
	output := tar.NewWriter(os.Stdout)
	defer output.Close()

	if err := compress(output, input, history, index); err != nil {
		return err
	}

	return nil
}

func prepare(base string) ([]string, map[string][]string, error) {

	// get history of base image
	history, err := docker.History(base)
	if err != nil {
		return nil, nil, err
	}

	// save the base image as a tar
	saved, cmd, err := docker.Save(history[0])
	if err != nil {
		return nil, nil, err
	}
	defer cmd.Wait()

	// index base image
	index, err := index(saved)
	if err != nil {
		return nil, nil, err
	}

	// cleanup
	if err := cmd.Wait(); err != nil {
		return nil, nil, err
	}

	return history, index, nil
}

func index(saved *tar.Reader) (map[string][]string, error) {

	index := make(map[string][]string)

	for {
		header, err := saved.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}

		if !strings.HasSuffix(header.Name, "/layer.tar") {
			continue
		}

		layer := strings.TrimSuffix(header.Name, "/layer.tar")
		glog.V(2).Infof("index: layer: %s", layer)

		reader := tar.NewReader(saved)

		for {
			header, err := reader.Next()
			if err == io.EOF {
				break
			}
			if err != nil {
				return nil, err
			}

			if header.Size == 0 {
				continue
			}

			// calculate hash
			hasher := sha1.New()
			if _, err := io.Copy(hasher, reader); err != nil {
				return nil, err
			}
			hash := hex.EncodeToString(hasher.Sum(nil))

			glog.V(2).Infof("index: layer: %s: %s = %s", layer, header.Name, hash)
			index[hash] = []string{layer, header.Name}
		}
	}

	glog.V(2).Infof("index: %d files", len(index))
	return index, nil
}

func compress(output *tar.Writer, input *tar.Reader, history []string, index map[string][]string) error {

	for {
		header, err := input.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		// straight copy metadata or small layer
		if !strings.HasSuffix(header.Name, "/layer.tar") {
			if err := output.WriteHeader(header); err != nil {
				return err
			}
			if _, err := io.Copy(output, input); err != nil {
				return err
			}
			if err := output.Flush(); err != nil {
				return err
			}
			continue
		}

		layer := strings.TrimSuffix(header.Name, "/layer.tar")
		found := false
		for _, l := range history {
			if l == layer {
				found = true
				break
			}
		}
		if found {
			glog.V(2).Infof("compress: %s: no changes", layer)
			continue
		}

		reader := tar.NewReader(input)
		buffer := bytes.NewBuffer(nil)
		writer := tar.NewWriter(buffer)
		defer writer.Close()
		if err := diff(writer, reader, index); err != nil {
			return err
		}
		if err := writer.Close(); err != nil {
			return err
		}

		header.Name = layer + "/diff.tar"
		header.Size = int64(buffer.Len())
		if err := output.WriteHeader(header); err != nil {
			return err
		}
		if _, err := io.Copy(output, buffer); err != nil {
			return err
		}
		if err := output.Flush(); err != nil {
			return err
		}
	}

	return nil
}

func diff(writer *tar.Writer, reader *tar.Reader, index map[string][]string) error {

	for {
		header, err := reader.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		// straight copy small files
		if header.Size <= 0 {
			if err := writer.WriteHeader(header); err != nil {
				return err
			}
			if _, err := io.Copy(writer, reader); err != nil {
				return err
			}
			if err := writer.Flush(); err != nil {
				return err
			}
			continue
		}

		// hash file and make a copy
		buffer := bytes.NewBuffer(nil)
		hasher := sha1.New()
		if _, err := io.Copy(io.MultiWriter(hasher, buffer), reader); err != nil {
			return err
		}
		hash := hex.EncodeToString(hasher.Sum(nil))

		// copy new file
		info, ok := index[hash]
		if !ok {
			if header.Size != int64(buffer.Len()) {
				panic("buffer length differs from size in header")
			}
			if err := writer.WriteHeader(header); err != nil {
				return err
			}
			if _, err := io.Copy(writer, buffer); err != nil {
				return err
			}
			if err := writer.Flush(); err != nil {
				return err
			}
			continue
		}

		// use index info
		header.Xattrs = make(map[string]string, 3)
		header.Xattrs["docker.juggle.layer"] = info[0]
		header.Xattrs["docker.juggle.name"] = base64.StdEncoding.EncodeToString([]byte(info[1]))
		header.Xattrs["docker.juggle.size"] = strconv.FormatInt(header.Size, 10)
		header.Size = 0

		if err := writer.WriteHeader(header); err != nil {
			return err
		}
		if err := writer.Flush(); err != nil {
			return err
		}
	}

	return nil
}
