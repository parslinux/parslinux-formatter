#!/bin/bash

langs=("tr" "pt" "en")

if ! command -v xgettext &> /dev/null; then
    echo "xgettext bulunamadı. Lütfen 'sudo apt install gettext' kurun."
    exit 1
fi

echo "Updating POT file..."
xgettext --from-code=UTF-8 -o po/parslinux-formatter.pot --files-from=po/files

for lang in "${langs[@]}"; do
    if [[ -f po/$lang.po ]]; then
        echo "Updating $lang.po..."
        msgmerge -o po/$lang.po po/$lang.po po/parslinux-formatter.pot
    else
        echo "Creating $lang.po..."
        cp po/parslinux-formatter.pot po/$lang.po
    fi
done