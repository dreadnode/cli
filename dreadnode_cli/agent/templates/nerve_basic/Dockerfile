# image is automatically built and pushed to the docker hub at every commit to mai
FROM evilsocket/nerve:latest

WORKDIR /app
COPY task.yml .

# the entrypoint is the nerve binary set by the base image

CMD [ \
    # the generator to use
    "-G", "http://dropship/v1", \
    # the task file
    "-Ttask.yml", \
    # openai tool calling json format does not support example payloads, so force our own XML format
    "--force-format"]