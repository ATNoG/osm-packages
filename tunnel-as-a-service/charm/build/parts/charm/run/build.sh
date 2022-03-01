#!/bin/sh
set -e
# Environment
## Part Environment
export CHARMCRAFT_ARCH_TRIPLET="x86_64-linux-gnu"
export CHARMCRAFT_TARGET_ARCH="amd64"
export CHARMCRAFT_PARALLEL_BUILD_COUNT="1"
export CHARMCRAFT_PART_NAME="charm"
export CHARMCRAFT_PART_SRC="/root/project/build/parts/charm/src"
export CHARMCRAFT_PART_BUILD="/root/project/build/parts/charm/build"
export CHARMCRAFT_PART_BUILD_WORK="/root/project/build/parts/charm/build"
export CHARMCRAFT_PART_INSTALL="/root/project/build/parts/charm/install"
export CHARMCRAFT_STAGE="/root/project/build/stage"
export CHARMCRAFT_PRIME="/root/project/build/prime"
export LDFLAGS="-L/root/project/build/stage/lib"
## Plugin Environment
## User Environment

set -x
env -i LANG=C.UTF-8 LC_ALL=C.UTF-8 PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin SNAP=/snap/charmcraft/x5 SNAP_ARCH=amd64 SNAP_NAME=charmcraft SNAP_VERSION=1.2.1 /snap/charmcraft/x5/bin/python3 -I /snap/charmcraft/x5/lib/charmcraft/charm_builder.py --charmdir /root/project/build/parts/charm/build --builddir /root/project/build/parts/charm/install --entrypoint /root/project/build/parts/charm/build/src/charm.py -r requirements.txt
