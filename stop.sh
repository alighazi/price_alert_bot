#!/bin/bash
for KILLPID in `ps ax | grep 'tg_bot_service' | awk '{print $1;}'`; do
kill -15 $KILLPID;
done
