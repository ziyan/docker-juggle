package docker

import (
	"archive/tar"
	"bufio"
	"github.com/golang/glog"
	"os/exec"
)

func History(image string) ([]string, error) {
	history := make([]string, 0, 10)

	cmd := exec.Command("docker", "history", "-q", "--no-trunc", image)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}

	if err := cmd.Start(); err != nil {
		return nil, err
	}
	defer cmd.Wait()

	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		history = append(history, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}

	if err := cmd.Wait(); err != nil {
		return nil, err
	}

	glog.V(2).Infof("docker: history: %v", history)
	return history, nil
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
