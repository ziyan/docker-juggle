package docker

import (
	"archive/tar"
	"github.com/golang/glog"
	"os/exec"
)

func History(image string) ([]string, error) {
	output, err := exec.Command("docker", "history", "-q", "--no-trunc", image).Output()
	if err != nil {
		return nil, err
	}

	glog.Warningf("docker-juggle-compress: %s", output)
	return nil, nil
}

func Save(image string) (*tar.Reader, *exec.Cmd, error) {
	cmd := exec.Command("docker", "save", image)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, nil, err
	}

	// start the command
	if err := cmd.Start(); err != nil {
		return nil, nil, err
	}

	return tar.NewReader(stdout), cmd, nil
}
