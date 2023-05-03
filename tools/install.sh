#!/bin/sh

if [ $# -ne 2 ]; then
    echo "Usage: tools/install.sh <os> <version>"
    exit 1
fi

os=${1}
version=${2}
target=""

if [ "${os}" = "mac" ]; then
    addon_dir="${HOME}/Library/Application Support/Blender/${version}/scripts/addons"
    mkdir -p "${addon_dir}"
    target="${addon_dir}/openai_bridge"
elif [ "${os}" = "linux" ]; then
    addon_dir="${HOME}/.config/blender/${version}/scripts/addons"
    mkdir -p "${addon_dir}"
    target="${addon_dir}/openai_bridge"
else
    echo "Invalid operating system."
    exit 1
fi

rm -rf "${target}"
cp -r src/openai_bridge "${target}"
