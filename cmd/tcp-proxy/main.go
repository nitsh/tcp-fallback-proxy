package main

import (
	"flag"
	"fmt"
	"net"
	"os"

	"github.com/nitsh/go-tcp-fallback-proxy"
)

var (
	matchid = uint64(0)
	connid  = uint64(0)
	logger  proxy.ColorLogger

	localAddr     = flag.String("l", ":9999", "local address")
	primaryAddr   = flag.String("p", "localhost:80", "primary remote address")
	secondaryAddr = flag.String("s", "localhost:81", "secondary remote address")
	verbose       = flag.Bool("v", false, "display server actions")
	veryverbose   = flag.Bool("vv", false, "display server actions and all tcp data")
	nagles        = flag.Bool("n", false, "disable nagles algorithm")
	hex           = flag.Bool("h", false, "output hex")
	colors        = flag.Bool("c", false, "output ansi colors")
)

func main() {
	flag.Parse()

	logger := proxy.ColorLogger{
		Verbose: *verbose,
		Color:   *colors,
	}

	logger.Info("Proxying from %v to %v with fallback to %v", *localAddr, *primaryAddr, *secondaryAddr)

	laddr, err := net.ResolveTCPAddr("tcp", *localAddr)
	if err != nil {
		logger.Warn("Failed to resolve local address: %s", err)
		os.Exit(1)
	}
	paddr, err := net.ResolveTCPAddr("tcp", *primaryAddr)
	if err != nil {
		logger.Warn("Failed to resolve remote address: %s", err)
		os.Exit(1)
	}
	saddr, err := net.ResolveTCPAddr("tcp", *secondaryAddr)
	if err != nil {
		logger.Warn("Failed to resolve remote address: %s", err)
		os.Exit(1)
	}
	listener, err := net.ListenTCP("tcp", laddr)
	if err != nil {
		logger.Warn("Failed to open local port to listen: %s", err)
		os.Exit(1)
	}

	if *veryverbose {
		*verbose = true
	}

	for {
		conn, err := listener.AcceptTCP()
		if err != nil {
			logger.Warn("Failed to accept connection '%s'", err)
			continue
		}
		connid++

		var p = proxy.New(conn, laddr, paddr, saddr)

		p.Nagles = *nagles
		p.OutputHex = *hex
		p.Log = proxy.ColorLogger{
			Verbose:     *verbose,
			VeryVerbose: *veryverbose,
			Prefix:      fmt.Sprintf("Connection #%03d ", connid),
			Color:       *colors,
		}

		go p.Start()
	}
}
