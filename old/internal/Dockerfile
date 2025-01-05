FROM golang:1.18-alpine

RUN wget https://github.com/githubnemo/CompileDaemon/archive/refs/tags/v1.4.0.tar.gz && \
    tar -xvf v1.4.0.tar.gz && \
    rm v1.4.0.tar.gz && \
    cd CompileDaemon-1.4.0 && \
    go build && \
    cp CompileDaemon /usr/local/bin/ && \
    rm -rf CompileDaemon-1.4.0

CMD cd /mnt/internal && CompileDaemon -command="go run main.go" -polling=true -color=true