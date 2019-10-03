# tcp-fallback-proxy

A TCP proxy written in Go inspired from jpillora/go-tcp-proxy

This project is created to support an easy fallback between active and standby services/servers.

## Usage

```
$ tcp-proxy --help
Usage of tcp-proxy:
  -c: output ansi colors
  -h: output hex
  -l="localhost:9999": local address
  -n: disable nagles algorithm
  -p="localhost:80": primary address
  -s="localhost:81": secondary address
  -v: display server actions
  -vv: display server actions and all tcp data
```