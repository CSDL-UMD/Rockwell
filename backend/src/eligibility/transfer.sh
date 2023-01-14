#!/bin/bash
set -euo pipefail

if [[ ${#} != 2 ]];
then
    >&2 echo "Error: wrong number of arguments: ${*}"
    >&2 echo "Usage: ${0} DIR DEST"
    >&2 echo "  DIR - local directory"
    >&2 echo "  DEST - s3 bucket"
    exit 1
fi
DIR=${1}
DEST=${2}
MINUTES=$((60*24*3))
logger "Starting transfer to ${DEST} from ${DIR}."
pushd "${DIR}" 1>/dev/null
mapfile -t FILES < <(find . -type f -cmin +${MINUTES} -and -iname \*.json.gz)
for file in "${FILES[@]}";
do
    aws s3 mv "${file}" "${DEST}"
done
popd 1>/dev/null
logger "Transferred ${#FILES[@]} files."
